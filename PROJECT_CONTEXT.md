# PROJECT_CONTEXT.md

## Project
FinSight AI: An AI-powered professional financial research and intelligence platform for US-listed companies.

## End Goal
A production-grade system that transforms raw financial statements into a professional research experience. The core objective is to reproduce the visual fidelity of the reference dashboard (`Artifacts/FinSight AI Apple Analytics Dashboard.png`) while ensuring absolute financial correctness. It will provide deep insights into company performance, business quality, and intrinsic value through a transparent, data-driven pipeline.

## Current Approach
Modular Layered Architecture with Medallion Data Flow:
`Sources` $\rightarrow$ `Ingestion (Bronze/Raw)` $\rightarrow$ `Validation` $\rightarrow$ `Cleaning (Silver)` $\rightarrow$ `Storage (Gold/Postgres)` $\rightarrow$ `Analysis Engine` $\rightarrow$ `API (FastAPI)` $\rightarrow$ `Dashboard (Streamlit)`.

## Current Progress
- **Phase 0 (Architecture):** Completed. Professional modular structure and tech stack finalized.
- **Phase 1 (Data Pipeline):** Functional. Implemented `YFinanceFetcher`, `FinancialValidator`, `FinancialCleaner`, and `DatabaseLoader`. Data flows from yfinance to PostgreSQL.
- **Phase 2 (Analysis Engine):** Basic. `FinancialMetrics` (YoY, CAGR), `RedFlagEngine` (basic rules), and `ValuationEngine` (Basic P/E, P/B, and simple DCF) are implemented.
- **Phase 3 (API Layer):** Functional. FastAPI endpoints exist for metrics, risks, and valuation.
- **Phase 4 (Dashboard):** Basic. A Streamlit app exists that connects to the API, but it lacks the visual hierarchy and complexity of the reference design.

## Design Reference
- **Visual Specification:** `Artifacts/FinSight AI Apple Analytics Dashboard.png`.
- **Requirement:** High visual fidelity to the reference image combined with absolute financial accuracy.

## Important Decisions
- **US-Market Focus:** The system is migrated to support US tickers and exchanges. Indian-market specific providers (e.g., Infoway) are disabled.
- **Medallion Architecture:** Strict separation between raw, silver, and gold data to ensure traceability.
- **Transparency:** Every calculated value must be traceable back to a source financial statement.
- **Planned Modules:** "WhaleWatch AI" is a future intelligence module for market anomalies and is currently a "Coming Soon" placeholder in the architecture.

## Pending Work
- **Dashboard Overhaul:** Reproduce the reference design's layout, typography, and visual hierarchy.
- **Valuation Depth:** Implement scenario analysis (Bear/Base/Bull) and sensitivity tools.
- **Risk Expansion:** Add more professional financial red-flag rules.
- **Peer Comparison:** Implement a module to benchmark companies against competitors.
- **Research Reports:** Automate the synthesis of data into a structured research report.

## Next Step
Establish the current application's runtime behavior and begin the "Visual Fidelity" phase by reproducing the reference dashboard's layout.

## Engineering & Learning Standards
- **Mentor-Led Development:** Concept $\rightarrow$ Implementation $\rightarrow$ Test $\rightarrow$ Improve.
- **Production Quality:** Type hints, Logging, OOP, and SRP (Single Responsibility Principle).
- **Verification:** No feature is "complete" until it is verified against real data.
