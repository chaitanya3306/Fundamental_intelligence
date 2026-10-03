# PROJECT_CONTEXT.md

## Project
AI-Powered Fundamental Analysis Intelligence Platform for Indian listed companies.

## End Goal
A production-quality system that collects financial data, cleans it, calculates fundamental metrics, detects red flags, performs valuation (DCF/Relative), and presents it via a FastAPI backend and a Streamlit dashboard.

## Current Approach
Modular Layered Architecture with Medallion Data Flow:
`Sources` $\rightarrow$ `Ingestion (Raw/Bronze)` $\rightarrow$ `Validation (Health Check)` $\rightarrow$ `Cleaning (Silver)` $\rightarrow$ `Storage (PostgreSQL/Gold)` $\rightarrow$ `Analysis Engine` $\rightarrow$ `API (FastAPI)` $\rightarrow$ `Dashboard (Streamlit)`.

## Current Progress
- **Phase 0 (Architecture):** Completed. (Professional modular structure, tech stack finalized).
- **Phase 1 (Data Collection):** Completed. (Implemented `YFinanceFetcher` class in `src/data_ingestion/fetch_basics.py` using OOP, logging, and error handling).
- **Phase 2 (Data Validation):** Completed. (Implemented `FinancialValidator` class in `src/data_validation/validator.py`. Established the "Health Inspector" logic to prevent GIGO).
- **Phase 3 (Cleaning):** Pending.
- **Phase 4 (Database):** Pending (Refactor to OOP required).
- **Phase 5+ (Analysis/Risk/Valuation):** Pending (Refactor to OOP required).

## Current State
The system can now fetch raw financial statements and validate their structural integrity (checks for empty files and required columns). The user has transitioned from "scripting" to "Software Engineering" by implementing the first two layers using professional OOP patterns.

## Important Decisions
- **Full OOP Refactor:** The project is being rewritten from scratch using a professional Object-Oriented approach (Classes, Type Hinting, SRP) instead of simple scripts.
- **Medallion Architecture:** Maintaining a strict separation between `raw` (untrusted) and `silver` (validated/cleaned) data.
- **Logging over Printing:** Using the `logging` module for all system messages to ensure production-readiness.
- **Error Isolation:** Implementing `try-except` blocks at the component level to prevent single-point failures.

## Important Learnings
- **GIGO Principle:** Validation must happen before storage to ensure data quality.
- **Stateful vs Stateless:** The distinction between `notebooks/` (exploration) and `src/` (production).
- **OOP Extensibility:** Why classes are superior to functions for modular components (e.g., easily swapping data sources).

## Pending Work
- Implement `src/data_cleaning/cleaner.py` (The "Chef" layer).
- Refactor `src/database/` into a `DatabaseManager` class.
- Refactor `src/financial_analysis/` and `src/risk_engine/` into professional OOP classes.
- Build the Valuation and API/Dashboard layers.

## Next Step
Start **Phase 3: Data Cleaning**. Implement the `DataCleaner` class in `src/data_cleaning/cleaner.py` to standardize the validated raw data into the "Silver" layer.

## Important Constraints
- **Teaching Style:** Strict mentor mode. Concept $\rightarrow$ Implementation $\rightarrow$ Test $\rightarrow$ Improve.
- **Verification:** Every phase must end with a verification exercise.
- **Engineering Standard:** Code must be production-level (Type hints, Logging, OOP, Error Handling).
