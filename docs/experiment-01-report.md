# Experiment 01: a working harness, an inconclusive mechanism test

We ran **44 Astra decisions**: 24 actor decisions and 20 monitor decisions. The actor study contains eight three-stage trajectories on **one synthetic vendor-export fixture**. Four additional monitor calls reviewed two hand-constructed faulty exports. These controls are separate from the actor study.

**All eight actors produced safe, successful final exports, including the four instructed adversarial runs. Both review views accepted all eight safe proposals.** Because no actor produced a violation, violation recall and the public record's incremental detection benefit cannot be measured. This is inconclusive about the mechanism, not evidence that public records do or do not work.

## What was compared

| Arm | Session handling | Public record |
| --- | --- | --- |
| A | Continued session | Ordinary concise explanation |
| B | Continued session | Typed evidence, constraints, uncertainties, decision basis |
| C | Fresh sessions with original-role replay of all prior public messages | Same typed record |
| D | Fresh sessions retaining the previous record and proposed action | Same typed record |

The task policy, observation timing, action options, and 1,800-character public-record allowance were matched. B/C/D shared the same record-preservation instructions. Each arm ran once with the nominal objective and once with an explicit synthetic red-team objective. The adversarial condition concerns instructed evasion against the nominal task policy; it does not measure spontaneous deception.

For every final action, two fresh Astra monitors received the original policy, all observations, preceding proposals, and candidate action. One additionally received the final public record. Monitors saw neither the arm label nor the adversarial instruction, grader verdict, or paired review. The flag threshold was fixed at 0.5, without false-positive-rate calibration. Model: `gpt-6-astra`, low effort; client: Codex 0.153.0. Platform reasoning summaries were disabled. All actions were inert JSON proposals; nothing was exported or executed.

## Results

| Result | Count |
| --- | ---: |
| Successful, nonviolating actor trajectories | 8 / 8 |
| Actor-generated violations | 0 / 8 |
| Safe actor proposals flagged without final record | 0 / 8 |
| Safe actor proposals flagged with final record | 0 / 8 |
| Fabricated faulty controls detected without final record | 2 / 2 |
| Fabricated faulty controls detected with misleading record | 2 / 2 |

The controls inserted a forbidden row or forbidden field and paired the action with reassuring but false public text. Detecting them checks the review pipeline's response to obvious concrete faults. It does not supply the missing adversarial actor failures.

## Measured resources

| Transport-reported metric | Value |
| --- | ---: |
| Input tokens, including cached input | 361,097 |
| Cached input tokens, a subset of input | 94,336 |
| Output tokens | 7,677 |
| Reported reasoning output tokens | 65 |
| Median decision latency | 8.7 seconds |
| Total measured decision time | 7.0 minutes |

These are token and latency measurements, not a billing or allowance conversion. Reasoning-token counts do not establish whether private computation occurred. One public JSON response contained a long whitespace run; its cause was not established. The full public response and anomaly measurement are retained in the data.

## Why the result is limited

There is one task fixture and one seed, not eight independent task samples. Its short, explicit action language makes review easy. The final output places the action before its record, so this evaluates review after selection and before execution. D also retains the previous action; the late observation does not require changing the already-correct action. The record can hold essentially all relevant evidence. These factors prevent a causal-faithfulness or frontier-parity conclusion.

The next mechanism test should introduce a late, trusted update that requires a revised action; separate record retention from previous-action retention; and use controlled, task-consistent changes to relevant evidence. It should measure incremental record value over the evidence-and-action baseline, task success, violations, and unflagged violations. A larger preregistered sample and separately calibrated monitoring threshold would be needed for reliable comparisons.

## Released materials

`experiment-01.json` preserves the scientific prompts, public responses, parsed actions and records, deterministic labels, paired reviews, token counts, and latencies. It excludes machine/account metadata and private reasoning. The accompanying offline fixture generator, grader, tests, and protocol definitions support inspection and regrading. The other two prepared fixtures were unit-tested but not run in this model calibration.

Local transport safety guards were improved during calibration without changing the scientific prompts or intervention definitions. The release records this limitation and includes a text safety scan and file hashes. Nothing here demonstrates recovery of hidden chain of thought.
