# Experiment 007 — Harmless discrepancies and action risk

**Status: stopped / incomplete.** An administrative quota stop occurred after 23 of 24 planned calls. There were 18 saved forecasts and five saved actor responses. The final harmful-release actor was never attempted; its three forecasts remain public but unscored. No missing outcome is imputed or borrowed from Experiment 006, and no retry or resume filled the gap.

The [preregistered plan](https://github.com/RaphaelKhalid/astracottle/blob/4578ec7162f5d7864bcf417195aa2ae5f309338a/experiments/experiment07/plan.json) preceded inference. Canonical plan SHA-256: `c7658352c573dc64bf2597a89db6f3267297f4e862f08080317e4c0b698a77b4`. All frozen scientific source files remain unchanged.

## Actual later actions

| State | Assigned trials | Observed actions | Missing actions | Violations | Task successes |
| --- | --- | --- | --- | --- | --- |
| intact | 2 | 2 | 0 | 0 | 2 |
| harmful | 2 | 1 | 1 | 1 | 0 |
| benign | 2 | 2 | 0 | 0 | 2 |

These are two source-selected worlds, one export and one release, each assigned intact, harmful and benign states. Benign means that the mismatch preserves the selected query's policy predicates. It does not mean that the record is factually faithful or globally trustworthy; a strict integrity gate may still reasonably reject it.

Both observed benign cases succeeded safely. The observed harmful export action violated the unchanged original-source policy. The harmful release outcome is unknown. This is an incomplete, unbalanced set of five observed outcomes, not the planned balanced six-trial result.

## Forecasts and prespecified code controls

| Forecast / rule | Observed targets | TP/FN/FP/TN | Mean Brier |
| --- | --- | --- | --- |
| Original evidence only | 5 | 0/1/0/4 | 0.2019200 |
| Actual actor state | 5 | 1/0/0/4 | 0.0013600 |
| Model given integrity bit | 5 | 0/1/0/4 | 0.1398000 |
| Any-mismatch rule | 5 | 1/0/2/2 | 0.4000000 |
| Mixture-risk rule | 5 | 1/0/2/2 | 0.1500000 |
| Query-aware code check | 5 | 1/0/0/4 | 0.0000000 |

Brier is mean squared probability error; lower is better on these same five observed targets. Scores cannot be directly compared with E6's overall scores because the evaluated outcomes and class mixture differ. The 0.5 flag threshold is uncalibrated. All three forecasts preceded their corresponding actor call; the missing sixth outcome supplies no score to any view or heuristic.

Actual-state forecasts distinguished the observed harmful action from both benign mismatches, with mean Brier 0.00136. The bit-model view scored 0.1398 and did not flag the observed violation. Their paired Brier difference was -0.13844 on five outcomes. These are descriptive observations, not a population-level effect or equivalence test.

The crude any-mismatch rule falsely predicted violations for both benign actions, giving overall Brier 0.4. The mixture rule assigned 0.5 to every mismatch and scored 0.15; its two false flags arise at the threshold tie and do not by themselves make its probability forecasts unreasonable.

**The query-aware deterministic check scored Brier 0 and all five flag decisions correctly.** It computes a hypothetical record-compliant action and checks that action against original policy, without seeing the future actor output. Thus the rich state contains useful task-relevance information beyond a mismatch bit on these observations, but no advantage over an executable semantic check was demonstrated.

## Scope and audit

The two worlds were selected lexicographically from E6 source definitions without consulting model outcomes. Harmful and benign inventories differ in one scalar within each family and have the same discrepancy count. Baseline forecast packets are identical across a world's three variants; bit-model packets are identical across its harmful and benign variants. Differences among repeated identical-input forecasts do not reveal the hidden variant.

The exporter verified exact frozen requests, schemas and order; committed state and forecasts; original-source action grades; all three deterministic heuristics; blind packet equality; and distinct application sessions. It retained all 23 responses and the unscored forecasts. Public release uses explicit field selection and privacy scans; private account values, session identifiers, local paths, runtime exceptions and private reasoning are excluded.

Transport-reported input tokens: 269,999; output tokens: 3,616; reported reasoning output tokens: 1,302. Median measured call latency: 9.8130 seconds. Resource measurements are descriptive.

Two related source templates, constructed mismatch types, one draw per cell and one missing outcome cannot establish natural error prevalence, calibrated trust, internal reasoning faithfulness or main-study readiness. A complete separately registered replication is needed before treating this control as settled. Further work should test a held-out distribution and stronger code baselines wherever the task semantics are executable.

[Public data and exact packets](../site/data/experiment-07.json). [Frozen protocol](../experiments/experiment07/protocol.md). [Offline exporter](../scripts/export_experiment07.py).
