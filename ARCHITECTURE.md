# FinSight AI Architecture

## Status
This document separates the audited repository architecture from the intended target. Target design is not a claim of implementation.

## Current repository structure (audited baseline)
- `src/data_ingestion/`: yfinance financial-statement fetching and raw staging.
- `src/data_validation/`: input/observation validation.
- `src/data_cleaning/`: normalization and Silver-style publication.
- `src/database/`: SQLAlchemy models, session management and loading.
- `src/pipeline/`: orchestration and run metadata.
- `src/financial_analysis/`: metric calculations and metric-name mapping.
- `src/risk_engine/`: initial financial red-flag rules.
- `src/valuation/`: initial DCF/valuation logic.
- `src/api/`: FastAPI app and Pydantic schemas.
- `src/dashboard/`: Streamlit implementation candidates; canonical entry point must be selected.
- `src/config/`: provider/configuration helpers.
- `alembic/`: migration environment and revisions.
- `tests/`: current test suite.

Reinspect the current branch before relying on any function-level claim.

## Target architecture
```text
Financial + market providers
          ↓
Provider adapters / source metadata
          ↓
Ingestion and Raw staging
          ↓
Structural + semantic validation
          ↓
Cleaning / alias mapping / standardization
          ↓
Canonical observations (Silver)
          ↓
PostgreSQL + reusable data access
          ↓
Financial calculations + market services
          ↓
Page/application services
          ↓
Typed FastAPI contracts
          ↓
Streamlit: Home / Overview / Statements /
          Quality / Growth / Valuation
```

Pipeline run metadata, lineage, freshness and quality outcomes should be observable.

## Layer responsibilities
**Provider/ingestion:** isolate provider quirks, retain source/fetch time, obey terms and rate limits; no financial formulas or UI logic.

**Validation/standardization:** validate schema, periods, duplicates and numerics; map aliases explicitly; preserve missing values and rejected-record reasons.

**Database:** stable observation identity; explicit annual/quarterly/TTM; currency/unit/provenance; migrations as schema authority; reusable queries.

**Analysis:** testable formulas; distinguish reported facts, derived values and assumptions; return period/unit/lineage/status.

**Application/API:** compose services into stable typed page contracts; represent unknown company, partial data, stale data and failures separately; do not run long refreshes inside normal request handling.

**Streamlit:** render service results; preserve selected company; no financial formulas in UI; handle loading, empty, stale, unavailable and error states.

## Core data concepts
Financial observations should preserve company/security identity, statement type, canonical and provider metric names, reporting start/end, fiscal year/quarter, frequency, value/status, currency/scale, source, retrieval time, run/provenance and validation result where available. Market observations need their own quote/event timestamp, interval, adjustment policy, source and freshness. Do not assume every provider supplies every dimension.

## Constraints
Python-first, Streamlit initial UI, FastAPI, PostgreSQL target, SQLAlchemy/Alembic. SQLite may support isolated tests where compatible. Prefer free/low-cost infrastructure. No secrets in repository. Ordinary tests should not require live provider availability.

Record schema, provider, API-contract or framework changes in DECISIONS.md with alternatives, trade-offs and migration impact.
