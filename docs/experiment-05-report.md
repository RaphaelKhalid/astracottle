# Experiment 005 — Carried state or independent reviewer aid?

**Status:** completed development diagnostic. No main-study readiness claim.

The [preregistered plan](https://github.com/RaphaelKhalid/astracottle/blob/50e37510b11a76c4278af8ad740bf644bf1ba923/experiments/experiment05/plan.json) preceded this diagnostic. Canonical plan SHA-256: `3ebf86c15ea3f06c3a1adb79e273440d05674489282fb91c49b049478b9e7d02`. The original E4 hidden-request candidates and carried records are fixed scientific inputs.

## Collection and populations

56 calls started and 56 responses were saved from 56 scheduled calls. The saved responses comprise 8 independent inventories, 24 natural-candidate reviews and 24 constructed-candidate reviews. No new actor actions were generated in this diagnostic.

The natural cohort contains 8 unchanged E4 actor candidates: 0 violations and 8 safe candidates. The constructed cohort contains 8 experimenter-edited candidates: 8 verified violations. Constructed faults are controlled diagnostic edits, not observed actor mistakes. Their prevalence and detection rate cannot estimate natural failure prevalence or sensitivity on natural actor errors.

## Review outcomes

| Cohort | View | Valid reviews | TP | FN | FP | TN | Missing | Mean Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Natural actor candidates | No inventory | 8 | 0 | 0 | 0 | 8 | 0 | 2.5125e-05 |
| Natural actor candidates | Carried inventory | 8 | 0 | 0 | 0 | 8 | 0 | 6.25e-07 |
| Natural actor candidates | Independent inventory | 8 | 0 | 0 | 0 | 8 | 0 | 7.5e-07 |
| Experimenter-constructed faults | No inventory | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| Experimenter-constructed faults | Carried inventory | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| Experimenter-constructed faults | Independent inventory | 8 | 8 | 0 | 0 | 0 | 0 | 0 |

Brier score is the mean squared error of the reported violation probability against the reference label; lower is better within the evaluated cohort. The two cohorts have different label mixtures and remain separate. Counts and scores are descriptive. The 0.5 flag threshold was fixed without false-positive calibration. No observed violations makes sensitivity undefined; no safe candidates makes false-positive rate undefined. Missing reviews are not safe results.

## Paired comparisons

| Cohort | Comparator | True label | Pairs | Carried only flags | Comparator only flags | Both flag | Neither flags | Mean probability shift | Mean Brier difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Natural actor candidates | No inventory | Safe | 8 | 0 | 0 | 0 | 8 | -0.002 | -2.45e-05 |
| Natural actor candidates | No inventory | Violation | 0 | 0 | 0 | 0 | 0 | Undefined | Undefined |
| Natural actor candidates | Independent inventory | Safe | 8 | 0 | 0 | 0 | 8 | -0.000125 | -1.25e-07 |
| Natural actor candidates | Independent inventory | Violation | 0 | 0 | 0 | 0 | 0 | Undefined | Undefined |
| Experimenter-constructed faults | No inventory | Safe | 0 | 0 | 0 | 0 | 0 | Undefined | Undefined |
| Experimenter-constructed faults | No inventory | Violation | 8 | 0 | 0 | 8 | 0 | 0 | 0 |
| Experimenter-constructed faults | Independent inventory | Safe | 0 | 0 | 0 | 0 | 0 | Undefined | Undefined |
| Experimenter-constructed faults | Independent inventory | Violation | 8 | 0 | 0 | 8 | 0 | 0 | 0 |

Differences are carried minus comparator on the same candidate. Positive probability shifts increase suspicion: this can help on violations and hurt on safe actions. Negative Brier differences favor carried evidence on those paired observations. The table reports raw disagreements without treating repeated views as independent source instances.

## Inventory equality and fidelity

Of 8 comparable inventory pairs, 8 are identical as canonical JSON with array order retained, and 8 contain the same source facts when array order is ignored. There are 16 carried-versus-independent review pairs with identical supplied inputs. Among those pairs, 0 have different flags and 16 have different full public responses.

When artifacts are canonically identical, any different review outputs are repeated stochastic measurements. They do not identify a content, carried-state or provenance effect. Semantic equality with different array order also does not prove a difference in supplied factual content; presentation may still differ.

| Inventory | Scored | Complete exact projection | Missing source facts | Extra output facts |
| --- | --- | --- | --- | --- |
| Carried | 8 | 8 | 0 | 0 |
| Independent | 8 | 8 | 0 | 0 |

Fidelity scores compare typed source facts while ignoring array order. A changed source fact can contribute both one missing original fact and one extra output fact. Incorrect inventories were retained without repair. These scores do not measure private reasoning faithfulness.

## Design and limitations

Each independent inventory used exactly the original hidden-request generation input, instructions, schema and capacity. It saw no selected query, actor candidate, carried record, grader label or earlier review. All independent inventories were committed before fresh reviews. The original evidence, query and candidate stayed identical across views; the neutral public_evidence field contained null, carried inventory or independent inventory. Eligible safe originals received one preregistered semantic action-boundary edit in the separate constructed cohort.

Carried-versus-independent performance combines artifact content, extraction quality, presentation and connection to the actor's supplied input. It does not isolate a pure causal effect of provenance. Eight worlds instantiate two related templates with one draw per view and shared model-family errors. Original world/record grouping must be preserved in any subsequent uncertainty calculation. Structured source-policy checks remain the practical reference.

## Audit and measured resources

The public exporter independently checked E4 scientific binding, exact hidden generation requests, source/action grades, deterministic fault eligibility, record commitments, source fidelity, neutral matched review packets and application-session separation. Explicit public fields exclude account state, session identifiers, private runtime wrappers, local paths and private reasoning.

Transport-reported input tokens: 684,326; output tokens: 27,088; reported reasoning output tokens: 227. No private reasoning text is published. Median measured call latency: 8.226 seconds; sum: 1083.02 seconds. These timings exclude preparation, audit and publication.

## Interpretation and next decision

All three reviewer views accepted every safe natural candidate and flagged every constructed violation. There were no missing reviews or flag disagreements. Thus the added inventory produced no observed flag-level gain on this fixed candidate set; constructed controls were already at the no-inventory review ceiling. This is not an equivalence result across future failures, and natural-error sensitivity remains undefined.

Every independent inventory exactly matched its carried counterpart, including array order. The 16 carried-versus-independent candidate pairs therefore supplied identical review inputs. Their different wording and tiny probability differences cannot identify a special carried-state or provenance effect. The natural-candidate Brier difference of -0.000000125 for carried minus independent is a descriptive difference between repeats, not evidence of a mechanism.

This diagnostic establishes a limitation of the current task distribution and removes a potential overclaim. Exact evidence copies can support decisions, but the observed review performance requires neither a model-generated inventory nor access to the actor's particular record. Deterministic checks remain available for these structured policies.

The separately preregistered Experiment 006 targets pre-action forecasting under controlled state faults. It tests actual actor outcomes after false supplied facts, with a one-bit integrity signal as a control. These are distinct from this experiment's post-hoc candidate edits. Neither experiment establishes natural failure prevalence or main-study readiness.

E5's review phase overlapped E6 collection. Reported timings describe those runs and should not be treated as isolated throughput benchmarks.

[Public data and exact packets](../site/data/experiment-05.json). [Frozen protocol](../experiments/experiment05/protocol.md). [Offline exporter](../scripts/export_experiment05.py).
