# Next development design: evidence before the request

**Design proposal following Experiment 003. Not preregistered; no model calls collected.**

## Question and mechanism

Experiment 003's records contained the final answer before the nominal action stage. A stronger test should commit an evidence representation before revealing which operational decision will be requested. The question is whether that record preserves information usable for a later, substantive decision and makes failures easier to locate.

For example, commit a permission registry covering several recipients and purposes, then reveal the particular export request. Or commit attestations across several builds/environments, then reveal which release status must be reported. Requests must be sampled independently from a frozen, balanced list; the record call cannot receive the selected request or a revealing identifier.

## Proposed controls

1. Compare request-known-at-commit and request-revealed-after-commit conditions on the same worlds and later requests. Keep evidence, policy, output schema, action interface and capacity fixed. This separates precomputing a requested answer from retaining reusable information, though timing also changes the record creator's task.
2. Restrict a separate extraction condition to typed source fields: event/source IDs, scope, revision, effective/expiry times and observed status. Avoid free-text recommendation fields. Audit against original evidence without repairing or filtering factual mistakes. This constrains overt answer encoding but does not prove that a model cannot encode unintended information.
3. Include a full-evidence fresh-action reference and a deterministic lossless source-field projection when the complete evidence fits the same capacity. These estimate losses from model extraction/compression separately from subsequent action selection. Never manufacture model-error rates merely by forcing necessary facts out of the capacity limit.
4. For each actual candidate, retain the paired monitor comparison: identical original evidence, late request and action; only one view additionally receives the committed record. When testing presentation assistance, add a separately produced task summary that was never sent to the actor, with a matched budget. That distinguishes generic reviewer assistance from information tied to the actor's carried state.

## Evaluation and limits

Score source-field preservation, provenance, action correctness, policy violations, task completion, and paired monitor decisions separately. Classify an error as record omission/misstatement, downstream action inconsistency, or unresolved rather than treating all failures as evidence of hidden intent. Publish all attempted cases and outputs. No invented fault should be counted as an actor-generated violation.

Manually altered record controls can test a reviewer's response to known omissions or contradictions, but must remain explicitly labelled diagnostics. They cannot supply the natural-error prevalence, sensitivity or power estimates for the main study.

Before collection, freeze the generator, development seeds, sampling weights, exact timing, record capacities, condition call graph, graders, monitor inputs and stopping rule in a new protocol. Choose a small fixed batch from measured usage; do not adapt within a cohort to obtain favorable monitor improvement. Keep new development data separate from later threshold calibration and held-out testing.

This design would resolve a specific confound; it would not by itself establish private-CoT faithfulness or guarantee enough monitoring headroom. Main-study calibration and sample-size requirements in [the readiness document](main-study-readiness.md) still apply.
