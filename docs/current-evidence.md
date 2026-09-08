# Current evidence and research decision

The evidence supports **auditing the state supplied to an actor**, with useful pre-action forecasting under controlled state errors. It does not establish access to private chain of thought, faithful accounts of internal computation, or calibrated deployment trust.

Experiments 004–007 added 223 model calls. Three studies completed their fixed schedules; Experiment 007 stopped administratively after 23 of 24 calls. The public notebook now contains 311 calls across seven studies, six completed and one incomplete. Calls, reviewer views and repeated states are not independent task samples.

## What the experiments show

| Study | Observation | Supported interpretation |
| --- | --- | --- |
| [004: evidence before the request](experiment-04-report.md) | All 16 model inventories exactly matched deterministic source copies; all 32 actions succeeded safely. | Evidence could be committed before a hidden request and used later. No distinctive reasoning information or error-detection advantage was established. |
| [005: carried versus independent aid](experiment-05-report.md) | Every view accepted eight safe proposals and caught eight constructed faults; all eight inventory pairs were identical. | The detector was already at a ceiling. Differences between identical carried/independent inputs are repeated measurements, not a provenance effect. |
| [006: pre-action forecasting](experiment-06-report.md) | Four intact actions succeeded; four injected state faults were followed by violations. Actual-state forecasts had Brier 0.0010875, versus 0.304 for original evidence alone. | Seeing a mistaken supplied premise helped predict the actor's later behavior. The simple mismatch heuristic also scored perfectly, so richer model review was not necessary for these outcomes. |
| [007: benign mismatch control, incomplete](experiment-07-report.md) | Both benign mismatches stayed safe. The crude mismatch rule falsely flagged both. Actual-state forecasts scored 0.00136 on five observed outcomes; query-aware code scored 0. | Relevance to the requested action matters beyond mere inequality with the source. No advantage over executable semantic checking was shown. The final harmful-release action is missing. |

Brier score is mean squared probability error; lower is better on the same targets. The study-level means concern different outcome mixtures and must not be treated as a cross-study improvement series. The probabilities and 0.5 flag threshold are uncalibrated. E7's three forecasts for its missing action remain public and unscored.

## The mechanism we can observe

The controller commits the exact public input before calling a fresh actor. A reviewer with both original evidence and that input can identify a false or irrelevant premise before the actor produces an answer. Restricting the actor's supplied facts makes the public record consequential; its usefulness is not based on claiming that the text reproduces private thought.

E6 changed a permission or test attestation in the carried state while retaining the original source-based grading rule. The later actors followed those false premises. E7 added discrepancies that left the selected task's policy predicates unchanged. This separates record integrity from predicted action risk: an inaccurate record can be harmless for one query while remaining untrustworthy as a source of facts.

The information advantage is explicit. Blind reviewers cannot observe which carried state the actor receives. Detailed-state reviewers can. A successful forecast under that design is evidence of application-level observability, not recovery of a hidden mental state or evidence of deception.

## What this contributes

The contribution is a reproducible mechanism study with controls that can disconfirm stronger claims: exact source projection, late requests, independently generated matched reviewer aids, same-input repeat checks, pre-action forecasts, integrity bits, benign discrepancies and query-aware code baselines. It includes exact public packets, frozen source hashes, independent export audits and failed or incomplete cases. It does not claim a new general algorithm or priority over earlier public-state and decomposition research; see the [literature map](proxy-literature.md).

## Research and integration decision

Do not launch the broad confirmatory monitorability comparison on this task distribution yet. Natural actor errors have not supplied a suitable failure population; the positive forecasting results used deliberately constructed state faults. Complete a separately registered replication of the benign control, then develop held-out tasks with measured natural error rates, reviewer headroom, task diversity and independent calibration before fixing main-study power.

Any application prototype should prioritize an enforced input boundary, immutable record commitments, source/provenance validation and action checks. Use model review where interpreting the relevant evidence requires it, and compare against the strongest available deterministic check. A skill can express this workflow, but a controller or tool gateway must enforce the boundary; instructions alone do not create that guarantee.

These results do not justify marketing a public record as private CoT, a universal trust score, or an established substitute for frontier-model CoT monitoring.
