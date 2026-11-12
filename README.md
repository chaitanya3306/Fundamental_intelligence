# FinSight AI

FinSight AI is a financial intelligence and fundamental-analysis application for supported US-listed companies. Its goal is to help users explore a company's business, financial statements, financial quality, historical growth and valuation.

> **Project status:** Early implementation. The six images in `Artifacts/` are product references, not evidence that all screens or data capabilities are implemented. See [PROJECT_PROGRESS.md](PROJECT_PROGRESS.md).

## Product

Six primary pages:
1. Home
2. Company Overview
3. Financial Statements
4. Financial Quality
5. Growth Analysis
6. Valuation

See [PRODUCT_SPEC.md](PRODUCT_SPEC.md) for page requirements and acceptance standards.

## Architecture target

`Financial/market providers → ingestion → validation → cleaning/standardization → PostgreSQL → financial analysis/services → FastAPI → Streamlit`

The repository already contains parts of this pipeline. See [ARCHITECTURE.md](ARCHITECTURE.md) for the audited baseline and target architecture.

## Technology direction

- Python, pandas, NumPy
- yfinance and other verified providers as appropriate
- PostgreSQL, SQLAlchemy, Alembic
- FastAPI, Pydantic
- Streamlit
- pytest

Provider availability, licensing, rate limits, currency, historical coverage and freshness must be verified before presenting data as supported. The app must not fabricate missing financial or market values.

## Development

- [CLAUDE.md](CLAUDE.md): Claude Code working rules
- [PRODUCT_SPEC.md](PRODUCT_SPEC.md): product requirements
- [PROJECT_PROGRESS.md](PROJECT_PROGRESS.md): verified current status
- [ROADMAP.md](ROADMAP.md): sequential development plan
- [ARCHITECTURE.md](ARCHITECTURE.md): current and target architecture
- [DECISIONS.md](DECISIONS.md): accepted decisions
- [Metric catalog](docs/financial/METRIC_CATALOG.md): financial definitions and calculation requirements

## Local setup

The project uses `uv` and `pyproject.toml`. After installing a compatible Python version and uv:

```bash
uv sync --frozen
uv run pytest -q
```

Check the current source/configuration for the exact database environment variables and application start commands before running the API or dashboard. Do not commit credentials or local database files.

## Scope

The initial MVP is fundamental analysis for supported US-listed companies. WhaleWatch AI and Combined Analysis are future extensions. Automated trading, brokerage integration and ML stock prediction are not part of the current MVP.
