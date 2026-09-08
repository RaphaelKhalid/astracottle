"""Offline event-stream regression tests: no subprocess, login, or model calls.

Run with: python work/pilot/transport_selftest.py
The three event-stream tests intentionally encode the required isolation behavior.
"""
import queue
import unittest
import transport

from transport import Server, weekly


def event(method, **params):
    return {"method": method, "params": params}


def answer(text, thread="current-thread", turn="current-turn"):
    return event("item/completed", threadId=thread, turnId=turn,
                 item={"type": "agentMessage", "id": "message-id",
                       "phase": "final_answer", "text": text})


def complete():
    return event("turn/completed", threadId="current-thread",
                 turn={"id": "current-turn", "status": "completed", "items": []})


class OfflineServer(Server):
    """Replace all communication with a finite, local notification stream."""
    def __init__(self, notifications):
        self.pending = []
        self.q = queue.Queue()
        self.calls = []
        self.sent = []
        for notification in notifications:
            self.q.put(notification)

    def call(self, method, params, timeout=45):
        self.calls.append((method, params))
        if method == "turn/start":
            return {"turn": {"id": "current-turn"}}
        if method == "turn/interrupt":
            return {}
        raise AssertionError("Unexpected offline method: " + method)

    def quota(self):
        return {"bucket": "codex", "windowDurationMins": 10080,
                "usedPercent": 10, "resetsAt": 1}

    def send(self, msg):
        self.sent.append(msg)


class TransportIsolationTests(unittest.TestCase):
    def setUp(self):
        previous = transport.STOP_PERCENT
        transport.STOP_PERCENT = 80
        self.addCleanup(setattr, transport, "STOP_PERCENT", previous)

    def run_turn(self, server):
        return server.turn("current-thread", "synthetic prompt", {"type": "object"}, timeout=1)

    def test_late_other_thread_output_is_not_accepted(self):
        server = OfflineServer([
            answer("STALE_OTHER_TRIAL", thread="previous-thread", turn="previous-turn"),
            answer('{"ok":true}'), complete()])
        result = self.run_turn(server)
        self.assertEqual(result["text"], '{"ok":true}')
        self.assertEqual(len(result["public_messages"]), 1)

    def test_model_reroute_invalidates_trajectory(self):
        server = OfflineServer([
            event("model/rerouted", threadId="current-thread", turnId="current-turn",
                  fromModel="gpt-6-astra", toModel="another-model", reason="rateLimit"),
            answer('{"ok":true}'), complete()])
        with self.assertRaises(RuntimeError):
            self.run_turn(server)
        self.assertTrue(any(method == "turn/interrupt" for method, _ in server.calls))

    def test_unexpected_server_request_cancels_active_turn(self):
        server = OfflineServer([
            {"id": 999, "method": "item/commandExecution/requestApproval",
             "params": {"threadId": "current-thread", "turnId": "current-turn"}},
            complete()])
        with self.assertRaises(RuntimeError):
            self.run_turn(server)
        self.assertTrue(any(method == "turn/interrupt" for method, _ in server.calls))

    def test_weekly_chooses_conservative_bucket_and_fails_closed(self):
        payload = {"rateLimitsByLimitId": {
            "a": {"secondary": {"windowDurationMins": 10080, "usedPercent": 10}},
            "b": {"primary": {"windowDurationMins": 10080, "usedPercent": 20}}}}
        self.assertEqual(weekly(payload)["usedPercent"], 20)
        with self.assertRaises(RuntimeError):
            weekly({})


if __name__ == "__main__":
    unittest.main(verbosity=2)
