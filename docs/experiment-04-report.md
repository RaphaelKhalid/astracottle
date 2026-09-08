# Experiment 004 — Evidence before the request

**Status:** completed development study. No main-study readiness claim.

The [preregistration](https://github.com/RaphaelKhalid/astracottle/commit/f8d2badd409d46549e5d6a2631037a2350abe777) preceded inference. Canonical plan SHA-256: `dfa36888516b64772223e202f83ffdb4dfebf794101761fa7af881bade0a5f55`. The frozen sources and plan remain unchanged.

## Interpretation and next decision

All 16 model inventories were exact source copies, with no missing or extra facts. Within every world, the request-known, request-hidden and deterministic inventories also matched canonically, including array order. Thus the three inventory action conditions supplied identical action inputs within each world. Any variation between these cells would be repeated model sampling on the same inputs, not a different informational state.

All 32 actions completed the legitimate task safely. All 56 reviews accepted them; reported violation probabilities were 0, 0.001 or 0.01. The 24 paired reviews had zero helped, zero harmed and 24 unchanged flag decisions. **Natural-error sensitivity and added detection value are undefined because no actor violations occurred.** This is not a demonstrated zero monitoring effect on failures.

Unlike Experiment 003, the committed records did not contain solved answers: they copied all typed facts before a hidden request was revealed. This supports a reusable evidence-memory mechanism on these eight worlds. It supplies no distinctive reasoning information beyond a deterministic source projection and does not establish private-computation faithfulness.

The next separately preregistered diagnostic fixes all eight request-hidden candidates and compares the actual carried inventory with an independently generated matched reviewer aid. Constructed candidate faults are kept separate from unchanged natural outputs. If the two inventories are identical, different reviewer outcomes will be treated as stochastic repeats of identical inputs. The main study remains unready: a natural failure distribution, reviewer headroom, calibration and a powered held-out design are still missing.

## Quantitative record

104 calls started; 104 responses saved, from a maximum of 104. The released dataset contains 16 model inventory responses, 32 action responses, and 56 monitor responses. There were eight assigned worlds per condition. Missing or invalid responses are not counted as safe results.

| Condition | Saved actions | Safe task completions | Violations | Invalid | Baseline TP/FN/FP/TN | With record TP/FN/FP/TN |
| --- | --- | --- | --- | --- | --- | --- |
| Request known at commitment | 8 | 8 | 0 | 0 | 0/0/0/8 | 0/0/0/8 |
| Request revealed after commitment | 8 | 8 | 0 | 0 | 0/0/0/8 | 0/0/0/8 |
| Deterministic source projection | 8 | 8 | 0 | 0 | 0/0/0/8 | 0/0/0/8 |
| Full original evidence | 8 | 8 | 0 | 0 | 0/0/0/8 | Not collected |

Baseline and record-assisted reviews concern the same candidate and original evidence. A zero violation count leaves detection sensitivity undefined. The 0.5 flag threshold is descriptive and uncalibrated. Condition-specific failures can differ, so comparing their recall does not isolate a controller effect.

## Evidence preservation

| Inventory timing | Scored inventories | Complete exact projections | Missing original facts | Extra output facts |
| --- | --- | --- | --- | --- |
| Request known at commitment | 8 | 8 | 0 | 0 |
| Request revealed after commitment | 8 | 8 | 0 | 0 |

Copy scores compare typed facts to the original source tables, ignoring array order. An altered fact contributes one missing original and one extra output fact. These are source-copy scores, not introspective faithfulness scores. Incorrect inventories were retained without oracle repair.

## Design

Four export and four release worlds each support four possible requests. The chosen request was fixed independently and balanced across scopes, then withheld from the hidden extractor. Both model inventory conditions used the same copy-all schema and 16,000-character capacity. Complete deterministic inventories required 8,578–9,190 characters. The deterministic projection preserved every typed source field, including misleading or stale entries; full-evidence actions retained the original packet wrappers too.

Each world committed both model inventories and the source projection before its four fresh actions. Three conditions received independent paired reviews with and without their actual committed record. The full-evidence condition had a baseline reviewer only. No external action executed.

## Audit and measurements

The independent exporter checked source hashes, query disclosure, the fixed call schedule, committed record hashes, action grades, extraction scores, and paired monitor packets. Public release uses explicit field selection and a separate privacy scan; raw account metadata, session identifiers, local paths, private runtime details and private reasoning are excluded.

Transport-reported input tokens: 1,173,211; output tokens: 52,540, including 1,292 reported reasoning tokens. No private reasoning text is released. Median measured call latency: 8.5935 seconds; sum: 2256.513 seconds. Timing excludes orchestration and review.

The study uses Astra's service identifier at low effort, not immutable model weights. Eight worlds share two structural templates and renamed identifiers, with one draw per cell. Public state may carry useful facts without exposing all internal computation. Both extractors were instructed to copy every fact, so request timing was allowed to have no effect. Deterministic policy checks remain the practical reference on these structured tasks.

[Public data and exact packets](../site/data/experiment-04.json). [Frozen protocol](../experiments/experiment04/protocol.md). [Offline release exporter](../scripts/export_experiment04.py).
