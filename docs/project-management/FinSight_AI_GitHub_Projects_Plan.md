# FinSight AI GitHub Projects Plan

This plan is based on the supplied 12-phase roadmap. It preserves its sequence and acceptance gates. Create one GitHub Issue per task group, then add issues to GitHub Projects. The connected GitHub actions here can create repository issues/files but cannot create or configure GitHub Projects V2 boards, custom fields, or add issues to a Projects V2 board. Create the board in GitHub UI and use Add item to add the issues.

## Project setup

- Project title: `FinSight AI | End-to-End Roadmap`
- Repository: `chaitanya3306/Fundamental_intelligence`
- Description: Track implementation of FinSight AI from verified current state to a complete, tested financial intelligence application while documenting practical data-engineering evidence.
- Status columns/values: `Backlog`, `Ready`, `In Progress`, `In Review`, `Testing`, `Done`, `Blocked`.
- Custom fields:
  - `Phase`: single select, Phase 1 through Phase 12
  - `Workstream`: single select, Data Engineering, Database, Financial Data, Financial Analysis, API, Streamlit UI, Testing, DevOps, Documentation
  - `Priority`: single select, P0, P1, P2
  - `Estimate`: number, relative effort units rather than promises in hours
  - `Acceptance Gate`: text
- Initial status: The supplied roadmap says Phase 1 has been implemented but also reports a loader failure in the latest supplied test output. Mark Phase 1 `In Progress` until local state is verified and a current test baseline is established. Do not mark work Done just because code exists.

## Issue template

Use this structure for implementation issues:

### Objective
What outcome must exist?

### Inspect first
Files, tests, and behavior to inspect before edits.

### Work
Small, ordered implementation steps.

### Acceptance criteria
Observable conditions required to close the issue.

### Verification
Exact commands/tests and evidence.

### Data-engineering concept
What this task teaches and why the design matters.

### Claude Code handoff
Inspect current code/tests first, explain the plan, make the smallest justified edits, run tests, and report changed files, actual command results, risks, and remaining work. Do not rewrite functioning modules wholesale or invent results.

---

# Phase 1: Stabilize the current implementation

**Initial status: In Progress / verify current local state.** The supplied test output reported eight failures in `tests/test_loader_data_quality.py` caused by an undefined `db_manager` reference in `src/database/loader.py`. Verify whether this still reproduces before editing.

## Tasks
1. **P1 | Reconcile local repository and GitHub state**
   - Inspect `git status`, branch, uncommitted changes, local commits ahead of `origin/main`, and reference files in `Artifacts/`.
   - Preserve local work; do not reset or overwrite.
   - Acceptance: current state and local-vs-remote differences are documented.
2. **P0 | Diagnose and fix database loader session dependency**
   - Inspect `src/database/loader.py`, `src/database/session.py`, `src/database/models.py`, `tests/test_loader.py`, and `tests/test_loader_data_quality.py`.
   - Determine the session-management pattern and fix the undefined reference with a minimal change.
   - Acceptance: relevant loader tests pass and behavior matches the intended session lifecycle.
3. **P0 | Establish full test baseline**
   - Run `uv run pytest -v`; classify pass/fail/skip and investigate failures.
   - Acceptance: results are recorded; failures are fixed or documented with follow-up issues.
4. **P1 | Verify reproducible local execution**
   - Verify API start, ingestion pipeline, database access, dashboard start, and test command.
   - Acceptance: exact working commands and required configuration are documented.

**Phase gate:** Loader dependency fixed; current test baseline known; app components start reproducibly; no local work discarded.

# Phase 2: Make the financial data pipeline reliable

1. **P1 | Define financial-statement data contracts**
   - Specify company, statement type, reporting period, metric, numeric value, currency/units where known, and ingestion provenance.
   - Define required vs optional inputs for supported calculations.
   - Acceptance: contract documented for income statement, balance sheet, and cash flow statement.
2. **P0 | Preserve missing financial values**
   - Inspect `src/data_cleaning/cleaner.py`; remove missing-to-zero substitution.
   - Distinguish reported zero, missing, invalid, not applicable, and provider-unsupplied values.
   - Acceptance: tests prove missing remains missing and true zero remains zero.
3. **P0 | Enforce validation inside pipeline**
   - Inspect `src/data_validation/validator.py` and `src/pipeline/run_pipeline.py`.
   - Ensure raw validation and cleaned/silver validation run at appropriate points; invalid data cannot silently reach persistence.
   - Acceptance: integration tests demonstrate validation blocks invalid data.
4. **P1 | Expand structural and numerical data-quality checks**
   - Cover reporting dates, duplicates, blank metric names, invalid numerics, infinity, missing required statements, schema drift, and contradictory values where rules are defensible.
   - Do not reject all nulls indiscriminately.
   - Acceptance: each check has a focused test.
5. **P1 | Make raw-data publication safe**
   - Stage full company refreshes, validate staged files, publish only after success, and retain previous valid data on failure.
   - Acceptance: simulated partial failure leaves last valid published raw data intact.
6. **P1 | Make pipeline reruns idempotent and transactional**
   - Verify keys, uniqueness, upserts, transactions, and behavior for provider/database failures and partial company failures.
   - Acceptance: repeated runs do not duplicate observations; failed writes do not leave partial company state; outcomes are observable.

**Phase gate:** Validation is integrated, null semantics are correct, failed refreshes preserve valid data, reruns are safe, and failures are understandable.

# Phase 3: Complete the database and financial data model

1. **P1 | Audit database models, migrations, and live schema**
   - Inspect `src/database/models.py`, `src/database/loader.py`, `src/database/session.py`, Alembic migrations, and actual schema.
   - Acceptance: differences are documented and resolved without unnecessary redesign.
2. **P1 | Verify financial-observation identity and constraints**
   - Review company, statement type, metric, reporting period, and required provider/accounting dimensions.
   - Acceptance: uniqueness constraints prevent duplicates without merging distinct observations.
3. **P1 | Preserve annual and quarterly period semantics**
   - Confirm provider representation and query behavior.
   - Acceptance: tests show annual and quarterly observations stay distinct and are not compared as equivalent periods accidentally.
4. **P2 | Document corrections/restatements policy**
   - Determine whether provider history supports revisions; implement supported behavior and document limitations where historical versions are unavailable.
   - Acceptance: correction behavior is tested or limitations are explicit.
5. **P1 | Build reusable analytical database queries**
   - Company profile, statements, historical series, latest observations, market data, freshness, and pipeline status.
   - Add indexes only when justified by access patterns.
   - Acceptance: queries have tests and support feature requirements.

**Phase gate:** Schema and migrations agree; period semantics and uniqueness are correct; historical behavior is documented; required read queries work.

# Phase 4: Complete financial and market-data coverage

1. **P0 | Build metric inventory from five reference artifacts**
   - For every displayed metric/chart/table/valuation output, document definition, inputs, source, frequency, history, formula, missing-data behavior, and validation.
   - Acceptance: every reference element maps to a real source/calculation or a clearly marked limitation.
2. **P1 | Audit current market-data implementation**
   - Inspect `src/config/api_data.py` and existing provider/cache logic for current/historical prices, shares outstanding, market cap, dividends, splits, beta, risk-free rate, and required DCF inputs.
   - Acceptance: supported and missing coverage is documented based on code/provider evidence.
3. **P1 | Implement only missing market-data ingestion required**
   - Keep market ingestion logically distinct from statement ingestion where source/frequency differ; reuse existing appropriate abstractions.
   - Acceptance: required market inputs are persisted/cached consistently or surfaced as unavailable.
4. **P1 | Define freshness and source provenance**
   - Define category-specific freshness, observation/retrieval timestamps, stale-data behavior, and recalculation dependencies.
   - Acceptance: incompatible/missing price, share, and period inputs cannot produce a falsely reliable metric.

**Phase gate:** All required metrics have an evidenced source/calculation and freshness/provenance behavior.

# Phase 5: Implement and verify the financial calculation engine

1. **P1 | Audit and define calculation boundaries**
   - Inspect `src/financial_analysis/metrics.py`, `src/financial_analysis/mapping.py`, `src/risk_engine/red_flags.py`, and `src/valuation/valuation.py`.
   - Separate reported values, normalized values, derived metrics, valuation outputs, and interpretations.
   - Acceptance: calculations are centralized rather than duplicated in UI code.
2. **P1 | Implement required metric families**
   - Growth, profitability, returns/efficiency, liquidity/leverage, cash generation, and market valuation, based on the metric inventory.
   - Acceptance: each required metric has a documented formula and input mapping; unrelated metrics are not added by default.
3. **P0 | Add formula and edge-case tests**
   - Cover units, currency, negatives, zero denominators, missing inputs, annual/quarterly comparability, and average vs period-end balance-sheet inputs where relevant.
   - Acceptance: controlled-input tests match independently checked expected results.
4. **P1 | Document calculation lineage**
   - Identify source fields, selected periods, formula, and missing-input policy for displayed metrics.
   - Acceptance: key metrics are traceable from inputs to output.

**Phase gate:** Required formulas are tested; edge cases have explicit behavior; lineage is explainable.

# Phase 6: Complete the Company Overview vertical slice

1. **P1 | Define company-profile API response contract**
   - Support available fields required by the reference, such as name/ticker, sector/industry when available, latest price, shares, market capitalization when valid, and timestamps.
   - Acceptance: Pydantic contract distinguishes unavailable data, unknown company, and server failure.
2. **P1 | Implement data-backed Company Overview endpoint**
   - Use established database/data-access patterns; avoid one external API call per metric card.
   - Acceptance: endpoint returns typed real data with normal/missing/error tests.
3. **P1 | Build Company Overview page matching reference**
   - Use `FinSight AI Apple Company Overview Dashboard.png`; connect cards/charts/tables to real API results.
   - Acceptance: material layout elements match reference and no fabricated values appear.
4. **P1 | Test source-to-UI path**
   - Trace fields through provider, ingestion, validation, persistence/cache, calculations, API, and Streamlit.
   - Acceptance: normal, missing, and API failure cases are verified.

**Phase gate:** Selecting a company displays real, correctly sourced supported profile/market data end-to-end.

# Phase 7: Implement Financial Statements

1. **P1 | Implement statement and period selection**
   - Income statement, balance sheet, cash flow statement, and annual/quarterly controls supported by data and reference.
   - Acceptance: selections query compatible periods and preserve the selected company.
2. **P1 | Implement statement tables and formatting**
   - Handle missing values, units, negatives, currencies, varying history length, and provider gaps.
   - Acceptance: tables reflect stored observations without rendering missing values as zero.
3. **P1 | Implement reference-backed historical charts**
   - Reuse the same data as tables; chart/table values reconcile.
   - Acceptance: period comparisons are correct and chart values match statement data.
4. **P1 | Test period correctness**
   - Prevent annual/quarterly mixing and invalid trend comparisons.
   - Acceptance: tests cover period boundaries and missing history.

**Phase gate:** Users can inspect all three statements and compatible historical periods; tables/charts reconcile.

# Phase 8: Implement Financial Quality

1. **P1 | Map Financial Quality reference requirements**
   - Inspect `FinSight AI Apple Quality Dashboard.png`; map each panel to category, inputs, formula/rule, and missing-data behavior.
   - Acceptance: full reference-derived inventory exists.
2. **P1 | Implement required quality measures**
   - Only required categories: earnings quality, cash conversion, returns, balance-sheet strength, margins, capital allocation, strengths/risks.
   - Acceptance: required indicators have calculations or explicit data limitations.
3. **P1 | Add evidence-backed risk interpretations**
   - Document data, formula/rule, threshold if applicable, rationale, and limitations.
   - Do not present a signal as proof of fraud/distress.
   - Acceptance: every flag has explainable evidence and test coverage.
4. **P1 | Connect API and reference-matched UI**
   - Acceptance: missing/incomplete history is handled clearly; displayed values tie to tested calculations.

**Phase gate:** Every required quality indicator has a tested calculation/rule and transparent interpretation.

# Phase 9: Implement DCF Valuation

1. **P1 | Audit DCF inputs and model assumptions**
   - Distinguish reported history, normalized starting values, user assumptions, forecasts, and outputs.
   - Acceptance: inputs and sources are documented.
2. **P0 | Complete and test DCF math**
   - Starting FCF, forecast growth, projected cash flows, discount rate, terminal value, present values, enterprise value, equity bridge, intrinsic value/share.
   - Acceptance: independent controlled examples validate calculations and edge cases.
3. **P1 | Wire all DCF controls to calculations**
   - Changing assumptions must recalculate forecasts and valuation, not just labels.
   - Acceptance: tests demonstrate expected output changes.
4. **P1 | Implement bear/base/bull scenarios**
   - Distinct assumptions and independently calculated results.
   - Acceptance: scenario assumptions and outputs are distinguishable and consistent.
5. **P1 | Implement sensitivity analysis**
   - Growth and discount-rate sensitivity as in reference; central case matches base assumptions.
   - Acceptance: independently calculated matrix and output reconciliation.
6. **P1 | Build DCF UI to reference**
   - Connect summary, forecast, assumptions, valuation breakdown, sensitivity, scenarios, and takeaways.
   - Acceptance: charts/tables reconcile with model results.

**Phase gate:** DCF outputs are independently verified; controls, scenarios, and sensitivity calculations work.

# Phase 10: Complete Home and shared application behavior

1. **P1 | Implement Home from reference**
   - Search/discovery, market overview, recently viewed/popular companies, and elements actually present in the image.
   - Use real data or explicit unavailable state.
   - Acceptance: no unsupported/fabricated indicators.
2. **P1 | Complete shared navigation and company state**
   - All five interfaces, active-page state, selected-company persistence.
   - Acceptance: navigation works without losing company selection.
3. **P2 | Extract justified reusable UI components**
   - Header, sidebar, company selector, metric cards, financial tables, chart panels, controls, loading/errors/freshness.
   - Acceptance: reuse improves consistency without awkward abstractions.
4. **P1 | Implement loading, stale, missing, empty, and error states**
   - API timeouts, provider failures, invalid input, absent history.
   - Acceptance: states are understandable and never fabricate values.
5. **P2 | Keep unimplemented modules explicitly Coming Soon**
   - WhaleWatch AI and Combined Analysis remain Coming Soon; do not add dedicated pages beyond the five approved reference pages.
   - Acceptance: scope matches specification.

**Phase gate:** Five approved interfaces behave as one cohesive app with consistent navigation and honest data states.

# Phase 11: Integrate and verify the product

1. **P0 | Build source-to-display reconciliation tests**
   - Trace representative values from source through database, calculation, API, and UI.
   - Acceptance: values reconcile at each boundary.
2. **P1 | Complete critical unit tests**
   - Cleaner, validator, financial metrics, DCF, risk rules, formatting when relevant.
   - Acceptance: critical edge cases tested.
3. **P1 | Add database/API integration tests**
   - Persistence, schemas, transaction rollback, upserts/reruns, API contracts.
   - Acceptance: controlled fixtures/mocks used where practical; ordinary tests do not depend on live provider availability.
4. **P1 | Add end-to-end user-flow verification**
   - Home → AAPL → overview → statements/period selection → quality → DCF/assumption changes.
   - Acceptance: selected company and outputs stay consistent.
5. **P1 | Run visual comparison against all five references**
   - Standard viewport; compare layout, spacing, typography, components, density, and hierarchy.
   - Acceptance: material differences fixed or explicitly documented.
6. **P0 | Run final full regression and document evidence**
   - Acceptance: final results and known limitations recorded; unexplained failures block completion.

**Phase gate:** The app operates as an integrated product and key figures reconcile.

# Phase 12: Production readiness and portfolio evidence

1. **P1 | Verify and persist pipeline-run history**
   - Check current run IDs, stage timings, status, processed counts, validation failures, errors, duration, and last success.
   - Persist durable history where operational requirements justify it.
   - Acceptance: runs can be diagnosed beyond transient console output.
2. **P2 | Add scheduling only after recovery is reliable**
   - Choose the simplest suitable scheduler; do not add Airflow solely as a résumé keyword.
   - Acceptance: refresh scheduling and failure policy documented/tested.
3. **P1 | Add structured logging and operational diagnostics**
   - Distinguish provider, validation, transformation, database, API, and UI failures; never log secrets.
   - Acceptance: actionable context exists for representative failures.
4. **P1 | Add CI checks**
   - Dependency install, tests, code quality, config, migration checks, startup/build.
   - Acceptance: automated checks run consistently in CI.
5. **P1 | Document refresh, backfill, and recovery procedures**
   - Refresh company, rerun pipeline, provider outage, historical reprocessing, corrections, invalid data, database/migration failure.
   - Acceptance: procedures are reproducible and tested where practical.
6. **P1 | Assemble data-engineering portfolio evidence**
   - Architecture, contracts, data dictionary, source limitations, quality rules, tests, safe-rerun evidence, failure/recovery demo, freshness/run history, reconciliation, deployment docs, trade-offs.
   - Acceptance: claims are supported by code, tests, commands, and observable behavior.
7. **P1 | Verify deployment and reproducible setup**
   - Budget-appropriate deployment; secrets/configuration managed safely.
   - Acceptance: clean setup/startup/deployment instructions work.

**Phase gate:** App can be run, tested, refreshed, diagnosed, and recovered with documented evidence.

---

# Definition of Done

## Product
- Five reference-backed interfaces: Home, Company Overview, Financial Statements, Valuation (DCF), Financial Quality.
- Company selection/navigation work.
- Required charts, tables, metrics, and valuation controls function.
- WhaleWatch AI and Combined Analysis remain Coming Soon.

## Data Engineering
- Sources, contracts, quality rules, freshness, and provenance documented.
- Missing is not silently converted to zero.
- Safe reruns avoid duplicates; failures do not corrupt last-known-good data.
- Database/migrations and period semantics are consistent.
- Refresh, recovery, and relevant backfill procedures documented.

## Financial correctness
- Required formulas tested; periods compared appropriately; DCF internally consistent; scenarios/sensitivity independently calculated; displayed outputs reconcile to underlying data.

## Engineering quality
- Unit, integration, failure-path, and end-to-end tests cover important behavior.
- Clean setup/run instructions work.
- Secrets are protected, CI is verified, and errors are diagnosable.
- Portfolio claims have evidence.

---

# Claude Code operating protocol

Use Claude Code as an inspect-first mentor and implementation partner, not an autonomous rewrite engine.

For each issue:
1. Read `CLAUDE.md`, this roadmap, the relevant issue, current code, and tests.
2. Report current behavior and evidence before proposing changes.
3. Explain the concept in the context of FinSight AI.
4. Write a small implementation plan and acceptance checklist.
5. Wait for approval for destructive, broad, schema-breaking, dependency-heavy, or unrelated changes.
6. Make the smallest justified change. Do not replace whole files when a focused patch is enough.
7. Add/update tests that prove behavior; do not create tests just to mirror an unverified assumption.
8. Run focused tests, then broader tests appropriate to the change.
9. Report exact commands and actual outcomes; never say tests passed if not run.
10. Update issue status only after evidence supports it. Never close a phase because code was merely written.
11. Finish each task with: what changed, why, files touched, tests/results, concept learned, risks/limitations, and next issue.
12. Never invent financial values, provider capabilities, repository files, test output, or implementation status.
13. Preserve user changes and ask before discarding/resetting/force-pushing/deleting important data.
14. Do not add Kafka, Spark, dbt, Airflow, Kubernetes, microservices, or a new data platform unless a demonstrated requirement justifies it.

## Suggested `CLAUDE.md` starter

```markdown
# FinSight AI: Claude Code Rules

## Role
Act as a senior data engineer, backend engineer, financial-data analyst, and patient mentor. Teach through implementation rather than only producing code.

## Source of truth
- Follow the project issue and approved 12-phase roadmap.
- Inspect source, tests, reference artifacts, and Git status before proposing edits.
- The repository may differ from plans or old audit notes. Verify claims against the current checkout.

## Safe changes
- Preserve user changes.
- Never reset, clean, discard, or overwrite unrelated work.
- Prefer small diffs over complete-file rewrites.
- Do not add dependencies or architecture without justification.
- Do not fabricate financial data or silently replace missing values with zero.
- Do not add pages outside the five approved interfaces; WhaleWatch AI and Combined Analysis are Coming Soon.

## Working loop
1. Inspect.
2. Explain current behavior.
3. State the problem and evidence.
4. Explain the concept being learned.
5. Propose a small plan and acceptance criteria.
6. Implement the smallest safe patch.
7. Add/update focused tests.
8. Run tests and report actual results.
9. Summarize changed files, trade-offs, failures, limitations, and next step.
10. Do not mark an issue complete without acceptance evidence.

## Test integrity
- Do not write tests based only on guessed behavior.
- Do not weaken/delete tests to manufacture a green suite.
- Separate unit tests, integration tests, and tests requiring external services.
- If a command cannot run, report that clearly.
- Report exact commands and actual pass/fail counts.

## Financial correctness
- Keep reported, normalized, derived, forecast, assumption, and valuation values distinct.
- Document formulas, units, period semantics, inputs, null policy, and limitations.
- Prevent annual/quarterly mixing.
- Never label a risk flag as proof of fraud.

## Git hygiene
- Inspect git status before edits and commits.
- Never commit secrets, credentials, private data, or large unnecessary provider dumps.
- Use small, descriptive commits.
- Do not push, merge, force-push, delete branches, or close issues unless explicitly requested.

## Task completion response
Return summary, files changed, why the change is correct, commands and actual results, concept learned, remaining risks, and recommended next issue.
```

## Claude Code issue-start prompt

```text
We are working on FinSight AI. Read CLAUDE.md, the End-to-End Implementation Roadmap, and the GitHub issue I provide.

Do not edit code immediately. First inspect the current repository, git status, relevant implementation, related tests, and reference artifacts. Treat old audit notes as hypotheses to verify, not facts.

Then:
1. Explain current behavior with file/function evidence.
2. Explain the data-engineering or financial concept needed for this task.
3. Identify the smallest implementation plan.
4. State acceptance criteria and test commands.
5. Point out any risk of destructive/schema-breaking changes.

Wait for my approval before implementation if the change is broad, destructive, schema-breaking, adds dependencies, or affects unrelated modules. Otherwise implement the smallest safe patch, add/update tests, run them, and report actual results. Do not rewrite whole files unnecessarily, weaken tests, fabricate data, or claim unrun tests passed. Do not mark the issue Done without acceptance evidence.
```

## Claude Code end-of-session prompt

```text
Before ending this session, summarize only verified state:
- Issue/task worked on
- Files changed
- Commands run and actual results
- Tests passing/failing/skipped
- Any uncommitted changes
- Concepts I learned
- Known risks or limitations
- Exact recommended next issue

Do not claim completion unless acceptance criteria have evidence. Do not update GitHub issue status unless asked, and do not discard changes.
```

# Daily workflow

1. Open the GitHub Project board and move one issue from `Ready` to `In Progress`.
2. Open the repository in Claude Code and give it the issue-start prompt plus issue number/title.
3. Work on that issue only unless investigation reveals a blocking dependency.
4. Review the diff yourself and ask Claude to explain confusing code.
5. Run tests, inspect output, and check for unrelated regressions.
6. Commit locally with a meaningful message after review.
7. Add test evidence and outcome to the issue.
8. Move to `Done` only when acceptance criteria are met; create follow-up issues for discovered work.

## GitHub Projects setup note

The connected GitHub actions available here can create repository issues and files, but do not expose operations to create/configure GitHub Projects V2 boards, custom fields, or add issues to a Projects V2 board. Create the board in GitHub's UI and add the issues via its Add item control. Do not assume a board exists until created.
