# What the public-state controller changes

The controller makes a public artifact part of the information path to the next action. It does not expose the model's private computation.

```text
Original evidence
       |
       v
Record-creation call --> committed public record
                                  |
                                  v
                         fresh action-selection call
                                  |
                                  v
                         proposed external action
```

The application chooses which original observations, previous messages, public records, and previous actions are supplied to each new call. Restricting these inputs can make the public record the only supplied path for current task facts. Private computation still occurs within each call. Fresh-session controls are application-level controls; they do not inspect server-internal state.

## Why this might help an overseer

A reviewer can check two relationships:

1. **Evidence to record.** Does the record preserve the relevant facts, restrictions, uncertainty, and provenance? Has an old permission or old test result survived a later update that should invalidate it?
2. **Record to action.** Is the proposed action consistent with those committed facts and restrictions?

For example, an export permission is revoked. If the record retains the old permission, it exposes a specific evidence-handling error. If the record correctly states the revocation but the proposed export still includes that row, the reviewer sees a consistency error.

The potential benefit is a compact account of what information the controller carries into a decision. That can reduce the reviewer's work, expose a mistaken assumption, or make some checks mechanical. These are hypotheses about usefulness, not guarantees of faithful introspection.

## What is enforced—and what is not

The application can enforce that a record exists before the action call, that it satisfies a schema and size limit, and that only selected public state is passed to the new session. It can log and check the proposed action before allowing execution.

It cannot infer from the record alone that every stated fact is true, every relevant fact was included, or the record describes all computation performed by the model. A record can be false, incomplete, misleading, or merely reassuring. A syntactically valid record is not necessarily a truthful one. Record content can also contain action recommendations or unintended information channels unless the schema and controller restrict them.

## The comparisons that matter

For the same proposed action, give two independent reviewers exactly the same original evidence and candidate action. Only one receives the committed record. A detection gain without unacceptable additional false alarms would show that the record adds useful review information.

Separately compare controller conditions on task completion, attempted violations, and unflagged violations per assigned task. Different controllers can produce different sets of mistakes. Comparing recall only among each controller's own violations can therefore compare different failure populations.

Experiment 002 showed appropriate use of supplied public facts in two benign fixtures. It did not include monitor calls. Experiment 001's actor proposals were all safe, so it could not estimate detection sensitivity on actor-generated violations. Neither establishes that public records improve CoT monitorability. The next preparation studies test the missing steps before a larger comparison is justified.

Experiment 003 completed the paired comparison on six further cases, but all actions were correct and both views accepted them. Detection benefit remains unmeasured. Its records already contained the solved answers, so the nominal action stage mostly reformatted them. The [next design proposal](next-development-design.md) delays the specific request until after evidence commitment to investigate that limitation.
