# astracottle

An independent public notebook on Astra, public working state, and AI oversight.

**Website:** https://astracottle.vercel.app

The question is whether an external controller can make useful evidence available to an overseer by controlling what public state an agent carries forward. Public records are decision artifacts. They are not recovered private chain of thought.

[Current evidence and research decision](docs/current-evidence.md).

## Experiments

- **001 — Export oversight calibration.** Forty-four model decisions on one synthetic export fixture: eight trajectories across four session/record conditions, plus two manually constructed positive controls. All actor proposals were safe. Both monitor views caught the planted faults. The result is inconclusive about incremental monitorability.
- **002 — Public state after a late trusted update.** Completed 20 calls on revoked export permission and invalidated release verification: 10 informed task completions and 6 appropriate deferrals among 16 final cells. Record creation and final action selection use separate sessions. Record retention is crossed with obsolete-action retention, with four additional record interventions. See the dated protocol and ledger for execution status.

- **003 — Oversight evidence screening.** Completed 24 calls across six cases: all actions correct, both monitor views accepted all. With no violations, added detection benefit remains unmeasured. Records already encoded the answers, motivating a separate request-after-commit design. [Report](docs/experiment-03-report.md).

- **004 — Evidence before the request.** Completed 104 calls: all 16 inventories were exact deterministic source copies; all 32 actions correct; all 56 reviews accepted. Evidence committed before the request was usable, but no actor failures were available to establish monitoring gain. [Report](docs/experiment-04-report.md).
- **005 — Carried state or independent reviewer aid?** Completed 56 calls: all views accepted eight safe candidates and detected eight constructed faults. All eight inventory pairs were identical, so carried-versus-independent differences are repeated reviews. [Report](docs/experiment-05-report.md).

- **006 — Forecasting future violations.** Completed 40 calls: actual-state forecasts identified four later violations under injected state faults; four intact actions succeeded. The simple mismatch heuristic also scored perfectly. This supports early input-state observability, with harmless mismatches still untested. [Report](docs/experiment-06-report.md).

- **007 — Harmless discrepancies and action risk.** Original collection stopped at 23/24 calls; a separately preregistered one-call extension on September 10 supplied the final outcome. Both harmful actors violated policy; both benign and both intact actors stayed safe. Actual-state forecasts caught both violations, and query-aware code matched all six outcomes. The combined analysis is exploratory. [Report and dated supplement](docs/experiment-07-report.md).

Results, failed setup gates, null findings, and limitations belong in the record. These small experiments are descriptive probes; they do not establish population-level performance or private reasoning faithfulness.

## Repository layout

- `site/`: static HTML, CSS, JavaScript, and reviewed public datasets; the only deployed output.
- `docs/`: protocols and reports.
- `experiments/`: reusable fixtures, deterministic evaluators, and an opt-in local runner.
- `scripts/`: release checks and a local static server.

The website has no backend, analytics, credentials, or model-call endpoint. Theme preference is stored locally in the browser.

## Website development

Requires Node.js 22 or later. There are no third-party runtime dependencies.

```sh
npm test
npm run dev
```

The local server prints its address. Vercel serves `site/` from the connected public GitHub repository. GitHub independently runs the release checks for each push.

## Running research locally

The Python fixtures and evaluators use the standard library. Model execution uses the supported Codex app-server, requires an existing ChatGPT sign-in, and consumes the operator's subscription allowance. No API key is embedded or required. The transport is currently Windows-specific and was calibrated with Codex 0.153.0 and Python 3.12.

Run offline self-tests first. The experiment runner requires an explicit `--run` and a frozen plan. Configure `ASTRACOTTLE_WEEKLY_STOP_PERCENT` locally to an absolute weekly-used ceiling appropriate for your account. An absent ceiling fails closed. This guard is conservative; it is not a guaranteed per-call spend cap. Never commit local run directories or account metadata.

The published experiment-02 through experiment-07 plans freeze exact source hashes. If you change source or use another transport, register a new protocol before collecting results rather than silently replacing the original.

## Public-release boundary

Data is exported through an explicit field allowlist. Credentials, account utilization and reset details, private conversations, machine paths, session identifiers, and private reasoning are excluded. Raw run directories are ignored by Git and Vercel. The public build is scanned for sensitive fields and credential patterns. Scans supplement review; they cannot certify arbitrary future files as safe.

Only the reviewed `site/` directory is web-served. The local execution code cannot be invoked through the website.

## Contributing

Open an issue for a methodological concern or a proposed replication. Separate observed results from hypotheses. Include fixture definitions, exact intervention semantics, a deterministic evaluator where possible, and a public-data review. Do not submit credentials or unreviewed private traces.

MIT licensed. Independent work; no affiliation with or endorsement by OpenAI is implied.
