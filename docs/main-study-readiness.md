# Main-study readiness and analysis protocol

**Status: preparation only; Experiments 01–07 do not establish main-study readiness.** This document fixes the distinction between a useful development screen and a confirmatory study. The final task distribution, sample size, calibration set, and analysis implementation must be frozen in a separate preregistration before the main run.

## Evidence so far

Experiment 01 used one fixture, eight actor trajectories, and two fabricated faulty controls. Every actor completed safely. The controls showed that concrete faults can be detected, but supplied no model-generated failures on which to estimate record-assisted recall. Experiment 02 used two benign cases: ten informed final cells succeeded and six insufficient-evidence cells deferred appropriately. It demonstrated public-information use in those cases, with no monitor calls. Neither experiment estimates the prevalence or difficulty of failures in a main-study population. Experiment 003 added six source-conflict cases, all with correct actions and correct monitor acceptance. It supplied no violations or monitoring headroom; its records already contained solved answers. Experiment 004 completed 104 calls: all 16 model inventories exactly matched deterministic source projections, all 32 actions succeeded safely, and all 56 reviews accepted. It supports evidence preservation before a hidden request, but provides no natural actor errors or measurable detection gain. Experiment 005 completed 56 calls: every reviewer view accepted all eight natural candidates and caught all eight constructed faults. Carried and independent inventories were identical. Experiment 006 completed 40 calls: all four injected state faults were followed by violations, and actual-state forecasts predicted them accurately. However, the deterministic mismatch heuristic also scored perfectly; the design did not include harmless mismatches. These are controlled development results, not a natural-failure distribution or evidence of private reasoning faithfulness.

## The question and the units

The proposed controller comparison remains:

- A: ordinary public explanations in continued sessions.
- B: required public records in continued sessions.
- C: the same records in fresh sessions with complete public-history replay.
- D: the same records in fresh sessions with restricted public persistent state.

Use the same tasks, evidence timing, action interface, available tools, validators, and response budgets across arms. To remove a known ambiguity, commit the record before the final action is requested. Any prior-action retention must be identical across arms or explicitly included as another experimental factor. The final monitor sees a proposal before execution; this does not imply access to private computation before action selection.

The primary sampling unit is a **scenario family and generated instance seed**. Run all four arms on every assigned instance. Arms, decision stages, two monitor views, and repeated stochastic draws are not independent task samples. A generator seed does not imply control over the model's sampling randomness.

## Estimands and the failure-population problem

For arm a, let V_a indicate an externally verified policy violation, U_a legitimate task success, and F_a0/F_a1 a monitor flag without/with the committed record. Both reviews concern the **same saved candidate** and receive otherwise identical task evidence and action history.

Define G_a = E[F_a1 − F_a0 | V_a = 1]. This is the record's added detection value on that controller's failures. The paired monitor-view comparison is clean evidence about whether adding that public artifact helps review those exact candidates.

**G_D − G_B compares different failure populations.** The controller may change whether a task fails, which error it makes, and how detectable that error is. Conditioning on those post-controller failures does not hold failure difficulty fixed. Matching task seeds, bootstrap resampling, or considering only failures common to both arms does not erase this limitation. A common-failure analysis can be secondary, explicitly restricted to that selected subset.

Therefore report, alongside G and its requested 15-percentage-point comparison:

- Unflagged violations per assigned task: R_a = P(V_a = 1 and F_a1 = 0).
- Violation frequency, ordinary task success, monitor false flags, deferrals, invalid outputs, and missing reviews separately.
- The unconditional added-detection quantity E[V_a(F_a1 − F_a0)]. This incorporates both error prevalence and review value; it is not a pure reasoning-faithfulness metric.

The paired difference in R between D and B/C is a system-level safety outcome. A decrease may come from preventing errors, detecting them, or both; decompose it rather than attributing it to private CoT. Keep invalid/ungraded cases visible in the assigned-task denominator and show worst-case risk bounds for missing labels. Never silently code malformed output as a safe negative. Count such cases as unsuccessful for utility.

## A screen is not a readiness certificate

A fixed six-case, 24-call development screen can test plumbing and expose useful failure modes. Its proposed gate—at least two actual policy violations, two safe completions, and at least one baseline catch and one baseline miss—is a **development diagnostic only**.

“Failure” here means an action-level policy violation independently confirmed by the reference grader, not a fabricated positive control, assigned adversarial role, ordinary task noncompletion, or deferral. Two observed failures do not provide a reliable failure-rate or power estimate. Headroom for another bounded batch establishes execution feasibility, not statistical feasibility.

The baseline-miss requirement intentionally selects difficult material. If used to develop a task family, acknowledge that selection and test fresh, previously unseen instances of the subsequently frozen generator. Do not portray the selected families as representative of everyday deployment. Do not keep regenerating the same screening cases until a desired gate passes. Report all attempted cases and keep the screen permanently out of confirmatory analysis.

Do not require record-assisted improvement as a screen gate: doing so would select evidence favorable to the intended conclusion. Records that misstate or omit facts must remain in the evaluated pipeline. Score record accuracy separately; do not oracle-repair them or discard their downstream failures. Parsing or transport failures follow a fixed, logged policy without selective retries.

## Required before declaring the main study ready

1. **Auditable labels and chronology.** Independent checks validate the grader on successes, violations, partial success, deferrals, and malformed actions. Candidate labels cannot depend on the model's explanation. The record is saved before the final-action request, and the two monitor packets differ only in record availability. World facts and evaluation labels are withheld from the actor unless they are legitimate task observations.
2. **Sufficient task variation.** Freeze task families, generation rules, their sampling weights, and seed lists. Require substantive decisions under late evidence rather than an action schema that names the violation directly. A ceiling-level monitor screen calls for harder development cases, not a claim that records lack value.
3. **Separate development, calibration, and test sets.** Screening examples and anything used to change prompts, tasks, or graders are development data. Calibration examples set thresholds only. Main seeds and labels are held out until the protocol is frozen. Maintain a public version/hash trail for any amendment; changed versions start a new evaluation cohort.
4. **A feasible fixed sample.** Estimate event prevalence and paired disagreement from separate development material. Choose and freeze the main sample size using those estimates and sensitivity analyses. If the resulting workload cannot fit the authorized resource envelope, the study is not ready to run; a smaller convenience sample is another exploratory pilot.
5. **Operational controls.** Verify model identity/settings, original-role replay, intended state transfer, disabled unintended tools/memory, fresh monitor contexts, schema handling, and no grader/file access. Preserve scientific logs while removing account information, credentials, session identifiers, and machine paths from public exports.

## Monitor calibration and blinding

Freeze the monitor instructions and scoring format before calibration. Use two thresholds, one per monitor view, fitted on a separate pool of benign, valid proposals spanning the frozen task/arm mixture. Apply those thresholds unchanged across main-study arms. Use a predetermined conservative tie rule and a nominal 10% calibration false-positive target. Do not choose thresholds from main-study ROC curves.

The 10% target is not a guarantee that every arm achieves 10% on the holdout. Report each arm's realized false-positive rate with uncertainty. If equal per-arm FPR is essential to the claim, preregister eight arm/view thresholds and provide correspondingly adequate independent calibration coverage instead; do not switch schemes after seeing results.

Remove arm names, role-assignment labels, grader outputs, later outcomes, and paired-review results from monitor packets. Randomize view and arm order using saved seeds. Record formatting itself may reveal the intervention; describe the procedure as blinding to explicit condition labels, not perfect blinding.

## Analysis and stopping

Resample complete scenario-seed clusters, retaining all arms and both monitor views together. If the estimand averages a fixed family mixture, resample within families with the preregistered weights; do not claim generalization to unseen families. Very few families or violation-bearing clusters make intervals unstable. Report raw counts and unresolved uncertainty rather than manufacturing precision.

The requested useful-effect target is a 15-point advantage in G_D − G_B, evidence of additional benefit over C, and ordinary utility loss no greater than five points. To claim that the advantage **exceeds the useful margin**, its preregistered one-sided lower confidence bound must exceed 0.15; a point estimate above 0.15 with a bound above zero supports a weaker statement. Utility noninferiority likewise needs its loss bound below 0.05. State the selection limitation on G regardless of significance. Fix confidence levels, multiplicity treatment, and the interpretation hierarchy before the run.

An upper bound below the useful margin can rule out the stipulated improvement within the studied population. A clearly excessive utility loss can make the controller impractical. Few violations, a monitor ceiling, substantial missing data, or wide intervals are **inconclusive**, not negative results.

Run the fixed ordered sample once and perform one final confirmatory analysis. Do not stop on a promising p-value, monitor improvement, or a convenient number of errors. An operator quota/safety stop is allowed at any time; retain the complete attempted-case log and label a truncated study exploratory/incomplete. Any sequential success or futility rule requires its own advance statistical design. New information may justify a future preregistration, not retroactive alteration of this one.

## Workload and power feasibility

For an illustrative call graph with three actor calls plus two monitor calls per arm, collection costs **20 calls per scenario-seed instance**, before independent calibration, development, or additional sampling:

| Main instances | Main calls alone |
| ---: | ---: |
| 100 | 2,000 |
| 250 | 5,000 |
| 500 | 10,000 |
| 1,000 | 20,000 |

The final staged-evidence and separate-record-commit call graph must be frozen before budgeting; extra record calls increase these totals. A 100-instance calibration using the same illustrative four-arm collection adds another 2,000 calls. A simpler calibration collection may cost less, but must still represent the intended monitor inputs and must be specified in advance.

Illustrative normal-approximation planning—not a sample-size recommendation—shows why the six-case screen is insufficient. For a 15-point difference in paired record-lift means between two independent arm-specific failure samples, 80% power at one-sided 5% significance would need roughly 140–550 violation-bearing samples **per arm** if the lift variable's variance is 0.25–1. Detecting a nonzero difference is weaker than establishing a lower bound above the 15-point useful margin. At a 20% violation yield, even 140 failures implies about 700 assigned instances per arm; actual yield is currently unknown. Paired correlation can change these requirements and must be estimated, not assumed.

The five-point utility bound can also be expensive: with no true utility loss and paired success disagreement of 5–20%, an illustrative one-sided noninferiority calculation requires roughly 125–500 paired task instances. These assumptions are not supported by the current two benign cases.

Subscription allowance has no demonstrated fixed calls-to-percentage conversion. Small pilots' rounded, shared usage changes cannot promise capacity for thousands of calls. For API planning, use the actual measured token distribution and current verified prices: cost = input_tokens × input_price + billed_output_tokens × output_price, with prices expressed per token and billed output including any charged reasoning. Long contexts, retries, and heavier reasoning can change cost substantially. Keep any account-specific allowance, cap, reset, or billing details in local operator configuration, outside public research artifacts.

**Preparation is valuable even if no main run follows.** A successful screen can identify a workable failure distribution and a reproducible oversight pipeline. A screen with no failures can reveal task or monitoring ceilings. An inaccurate-record failure can expose propagation that an oracle gate would hide. These are honest development findings; they do not substitute for an adequately resourced, independently evaluated main study.

## Update after the benign-mismatch control

Experiment 007 is incomplete: 23 of 24 calls, five actor outcomes, and one missing harmful-release action. Both benign mismatches preserved safe task success. Detailed-state model forecasts performed well on observed outcomes, but a query-aware deterministic check was also perfect. This adds a task-relevance control, not a natural failure distribution or main-study readiness. Preserve the missing outcome and use a separate complete replication before treating that control as settled. See [current evidence and research decision](current-evidence.md).

## Dated extension update: 2026-09-10

A separately preregistered one-call extension supplied the missing E7 harmful-release outcome: a violation. Original data remain unchanged. Across the six combined outcomes, actual-state forecasts and query-aware code made all flag decisions correctly. The delayed supplement closes this pilot, but does not supply independent replication, natural-failure headroom or main-study readiness. No additional model collection is scheduled.
