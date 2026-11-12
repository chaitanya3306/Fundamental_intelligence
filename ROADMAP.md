# FinSight AI Implementation Roadmap

Single authoritative roadmap. Product requirements: PRODUCT_SPEC.md. Verified status: PROJECT_PROGRESS.md.

Use vertical slices: complete provider → database → calculation → API → UI for a real user journey before multiplying pages. A phase is complete only when its gate is evidenced by code, tests and UI verification where applicable.

## Phase 0 — Repository stabilization
- Inspect branch, Git status, user changes and current code.
- Rotate any real committed credential; move secrets to environment configuration and assess history cleanup.
- Fix test collection defects; record fresh collection and full-suite results.
- Establish reproducible setup, test, pipeline, API and dashboard commands.
- Select one canonical dashboard entry point after reviewing both.
- Align README/config with actual supported US-market scope.
**Gate:** no user work lost; no new embedded secrets; test baseline and reproducible commands recorded; docs agree.

## Phase 1 — Reliable financial data pipeline
- Define contracts for income statement, balance sheet and cash flow.
- Preserve company, statement, metric, period, frequency, currency/unit, source, retrieval time and status where supported.
- Distinguish zero, missing, unavailable, invalid and not applicable.
- Validate staged raw data before publishing; retain last-known-good data on failure.
- Normalize provider aliases; validate cleaned/Silver outputs.
- Add safe publication, transactional/idempotent loading and observable failure counts.
**Gate:** invalid refresh cannot replace good data; null semantics correct; reruns do not duplicate; failure/recovery tests pass.

## Phase 2 — Database and historical observation model
- Reconcile ORM models, Alembic migrations and actual schema.
- Define stable observation identity and annual/quarterly/TTM semantics.
- Store currency/unit and provenance when available; use suitable numeric representation.
- Add justified indexes and reusable data-access queries.
- Test clean migration, upgrade, uniqueness, rollback and period separation.
**Gate:** model/migration parity; no period collisions; persistence tests pass.

## Phase 3 — Market and company reference data
- Verify provider coverage/terms/rate limits for US ticker search, profile, prices, volume, shares, market cap inputs, dividends, indices and movers.
- Separate market observations from statement observations.
- Define timestamps, cache/freshness and stale behavior.
- Defer unsupported data rather than inventing it.
**Gate:** each market element has an evidenced source/freshness rule or is explicitly deferred.

## Phase 4 — Financial calculation engine
- Complete docs/financial/METRIC_CATALOG.md and canonical metric mappings.
- Implement required profitability, returns, liquidity, leverage, cash-flow and growth metrics.
- Correct CFO/FCF semantics, YoY/CAGR units, elapsed-period handling and edge cases.
- Define financial-quality methodology and minimum evidence thresholds.
- Keep formulas outside UI.
**Gate:** every displayed formula has independent expected-value tests, lineage and explicit missing-data behavior.

## Phase 5 — API contracts and Company Overview vertical slice
- Define typed company/profile/market/fundamental/price-series responses.
- Reconcile FastAPI schemas with Streamlit consumers.
- Use a coherent sync/async design; avoid blocking work in async handlers.
- Complete Company Overview from source/database through API to UI.
- Test normal, missing, invalid-company, stale and provider-error cases.
**Gate:** supported ticker renders real, traceable data and values reconcile.

## Phase 6 — Financial Statements
- Income statement, balance sheet and cash flow services/endpoints.
- Annual/quarterly selection and explicit currency/scale.
- Tables/charts from consistent data; test gaps, signs and period boundaries.
**Gate:** all available statements display correctly and charts reconcile with tables.

## Phase 7 — Financial Quality
- Earnings quality, cash conversion, returns, balance-sheet strength, margins and capital allocation.
- Document score weights, thresholds, coverage and version.
- Evidence-backed strengths/risks; no healthy score with insufficient evidence.
**Gate:** all displayed metrics/scores/rules are traceable and tested.

## Phase 8 — Growth Analysis
- Revenue, net income, EPS, operating income and FCF series.
- Annual/quarterly YoY and CAGR; segment growth only where sourced.
- Charts, tables, comparisons and evidence-based insights.
**Gate:** growth outputs reconcile and periods/endpoints are valid.

## Phase 9 — Valuation
- Document DCF conventions and starting FCF.
- Correct forecast, discounting, terminal value, EV, equity bridge and diluted per-share value.
- Relative multiples and DDM only where inputs support them.
- Implement genuinely distinct bull/base/bear scenarios and calculated sensitivity.
**Gate:** independent controlled examples pass; controls recalculate; central sensitivity reconciles to base case.

## Phase 10 — Home and shared application
- Company search and popular shortcuts.
- Market overview, movers and news only with real supported sources.
- Shared company context, navigation and common loading/error/stale states.
**Gate:** six pages work as one app and unsupported sections are honestly unavailable/deferred.

## Phase 11 — Product verification
- Source-to-display reconciliation tests.
- Unit, database integration, API contract and failure-path tests.
- End-to-end search → overview → statements → quality → growth → valuation flow.
- Compare all six pages with Artifacts at a consistent viewport.
- Measure performance before optimizing.
**Gate:** critical flows pass, values reconcile, no fabricated outputs, visual gaps reviewed and full regression passes.

## Phase 12 — Operational and portfolio readiness
- CI for dependency sync, test collection, full tests and migrations where practical.
- Structured logs, pipeline run/failure observability and recovery procedures.
- Scheduling only after refresh/recovery are reliable.
- Reproducible setup and budget-appropriate deployment.
- Document architecture, contracts, data dictionary, metric lineage, trade-offs and limitations.
**Gate:** clean setup/test/run is reproducible; failures diagnosable; portfolio claims have evidence.

## Cross-phase rules
- Verify existing modules against acceptance criteria before reimplementing.
- Do not hardcode screenshot values.
- Do not add ML/LLM features before core fundamentals are reliable.
- Passing tests alone does not prove financial correctness.
- Update PROJECT_PROGRESS.md only with evidence.
