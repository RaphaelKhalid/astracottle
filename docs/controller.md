# Offline controller replay

The `controller` package is a small local policy boundary for replaying a
saved Astra proposal. It checks an operator-provided source snapshot and
proposal before writing a local export. It does not call a model, send data to
a real third-party route, or publish a result.

## Quick start

From the repository root, create the operator-selected output root once, then run a saved case with a fresh run identifier:

```sh
mkdir -p ../work/controller-demo
python -m controller replay --case examples/<case>.json --out ../work/controller-demo --run-id <id>
python -m controller replay --case examples/intact.json --out ../work/controller-demo --run-id astra-intact-replay
```

For an allowed export, the controller creates one directory named by the run
identifier containing exactly `receipt.json`, `receipt.html`, and
`export.csv`. A denied or deferred proposal still produces a reviewable local
receipt, but does not produce `export.csv`. Run identifiers are single-use;
replaying one into the same output root is denied.

Each case supplies a source snapshot with this shape:

```json
{
  "records": [{"case_id": "...", "error_code": "..."}],
  "policy": {
    "route_alias": "...",
    "purpose": "...",
    "recipient": "...",
    "allowed_record_ids": ["..."],
    "allowed_columns": ["..."]
  }
}
```

The proposal contains `operation` (`export` or `defer`), the route alias and
purpose, and explicit `record_ids` and `columns`. The public Python API is:

```python
from controller.core import execute, inspect_proposal

review = inspect_proposal(source, proposal)
receipt = execute(source, actor_input, proposal, output_root, run_id)
```

`inspect_proposal` returns `allowed`, a list of checks with `id`, `passed`,
and `detail`, and human-readable `reasons`. The checks enforce the source
schema, exact operator-provided route and purpose, allowed record and column
lists, and safe identifiers and paths. `execute` rechecks those conditions,
uses a fresh run directory below `output_root`, and writes deterministic local
receipts and CSV output.

## What this demonstrates

The included replay is a saved Astra proposal with a deterministic
intervention. It is a plumbing and boundary demonstration, not a fresh
efficacy trial. It shows that a matching proposal can be exported locally and
that malformed, unauthorized, duplicate, or path-escaping requests are
refused. The E7 task-aware deterministic checker also matched all six
outcomes; this implementation packages deterministic checks and does not claim
a superior monitor.

The policy is supplied by the operator. Passing the checks verifies that the
proposal conforms to that supplied policy, but it does not prove the policy's
truth, authorization, or authenticity. Hashes bind the recorded content for
this run; they are not a tamper-proof proof against a localhost owner. Evidence
in the source snapshot is recorded separately from actor input and is not
independently established by the controller. The controller does not claim
private chain of thought or private-reasoning access.

The offline replay writes only to the requested local output root and does not
send to a real third-party service. An opt-in live adapter, if added and
explicitly selected, necessarily sends the selected evidence to its model
service; that is outside this offline replay guarantee. A modified or
compromised controller or host is outside this scope. Receipts and CSV exports
can contain private data. Offline replay leaves them local and never makes them
public automatically; review and remove private values before sharing any
output.
## Explicit live proposal mode

A separate opt-in command can ask the reviewed subscription transport for one
Astra proposal and then submit that proposal to the same local controller:

```sh
python -m controller propose --case examples/<case>.json --out ../work/controller-live --run-id <id> --weekly-stop 50
```

The weekly stop is required and must be an integer from 1 to 100. The adapter
uses one fresh Astra low-reasoning session with tools disabled, sends the case's
`actor_input` inside a concise JSON request, and makes no retries. The source
snapshot is validated locally and is not sent as an authority correction to the
model. A completed, schema-valid model proposal is checked again by the local
controller before any CSV is written. Failed, cancelled, malformed, or
unauthorized responses produce a blocked receipt and no CSV.

Live mode necessarily sends the selected actor input and concise request to the
reviewed model service. Its local receipt records that disclosure, the model
identifier, response status, and sanitized public output; it never stores raw
transport logs, session/account metadata, or private reasoning. The local
executor does not upload outputs. Use `replay` when no model-service transfer
is desired.