# Example Pipeline Run (Phase 1 baseline)

The following is the console output from a **single execution** of the pipeline (`python -m src.pipeline.run_pipeline`). It demonstrates the behaviour when the Silver layer contains no data for any of the default tickers, which results in a *failure* status. This output is useful for verifying that the pipeline stages run correctly and that the audit tables are populated (or not) as expected.

```
2026-10-26 20:17:36,883 - INFO - Pipeline started: run_id=1a7d142f-53a4-4e01-ace3-0a1a8ca9f87e requested_tickers=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA']
2026-10-26 20:17:36,883 - INFO - Fetching financial statements for US ticker AAPL
2026-10-26 20:17:45,438 - WARNING - Incomplete refresh for AAPL; unavailable statements: income_statement, balance_sheet, cashflow
2026-10-26 20:17:45,439 - INFO - Fetching financial statements for US ticker MSFT
2026-10-26 20:17:52,880 - WARNING - Incomplete refresh for MSFT; unavailable statements: income_statement, balance_sheet, cashflow
2026-10-26 20:17:52,880 - INFO - Fetching financial statements for US ticker GOOGL
2026-10-26 20:18:00,419 - WARNING - Incomplete refresh for GOOGL; unavailable statements: income_statement, balance_sheet, cashflow
2026-10-26 20:18:00,422 - INFO - Fetching financial statements for US ticker AMZN
2026-10-26 20:18:07,925 - WARNING - Incomplete refresh for AMZN; unavailable statements: income_statement, balance_sheet, cashflow
2026-10-26 20:18:07,925 - INFO - Fetching financial statements for US ticker META
2026-10-26 20:18:15,349 - WARNING - Incomplete refresh for META; unavailable statements: income_statement, balance_sheet, cashflow
2026-10-26 20:18:15,349 - INFO - Fetching financial statements for US ticker TSLA
2026-10-26 20:18:19,780 - WARNING - Incomplete refresh for TSLA; unavailable statements: income_statement, balance_sheet, cashflow
2026-10-26 20:18:19,780 - INFO - Fetching financial statements for US ticker NVDA
2026-10-26 20:18:20,588 - WARNING - Incomplete refresh for NVDA; unavailable statements: income_statement, balance_sheet, cashflow
2026-10-26 20:18:20,589 - INFO - Ingestion finished: run_id=1a7d142f-53a4-4e01-ace3-0a1a8ca9f87e succeeded=0 failed=7
2026-10-26 20:18:20,589 - INFO - Cleaning finished: run_id=1a7d142f-53a4-4e01-ace3-0a1a8ca9f87e succeeded=0 failed=0
2026-10-26 20:18:20,589 - INFO - Database loading finished: run_id=1a7d142f-53a4-4e01-ace3-0a1a8ca9f87e attempted=0 failed=0
2026-10-26 20:18:20,589 - INFO - Pipeline completed: run_id=1a7d142f-53a4-4e01-ace3-0a1a8ca9f87e status=failure duration_seconds=43.7065
2026-10-26 20:18:20,589 - INFO - Pipeline execution report: {'run_id': '1a7d142f-53a4-4e01-ace3-0a1a8ca9f87e', 'started_at': '2026-10-26T14:47:36.883329+00:00', 'completed_at': '2026-10-26T14:48:20.589806+00:00', 'status': 'failure', 'requested': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA'], 'fetch_failed': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA'], 'clean_failed': [], 'load_failed': [], 'stage_durations_seconds': {'fetch': 43.7055, 'clean': 0.0006, 'load': 0.0}, 'duration_seconds': 43.7065, 'failed_stage': None, 'failure_reason': None}
2026-10-26 20:18:20,659 - ERROR - Pipeline finished with status=failure. Report: {'run_id': '1a7d142f-53a4-4e01-ace3-0a1a8ca9f87e', 'started_at': '2026-10-26T14:47:36.883329+00:00', 'completed_at': '2026-10-26T14:48:20.589806+00:00', 'status': 'failure', 'requested': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA'], 'fetch_failed': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA'], 'clean_failed': [], 'load_failed': [], 'stage_durations_seconds': {'fetch': 43.7055, 'clean': 0.0006, 'load': 0.0}, 'duration_seconds': 43.7065, 'failed_stage': None, 'failure_reason': None}
```

*Note:* This run reflects the current repository state where the Silver data directory is empty. Once real Silver files are placed (e.g., via the fetcher or manual import), the pipeline should report **success** and populate the `pipeline_runs` and `pipeline_company_runs` tables.
