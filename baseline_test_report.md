# Baseline Test Report

This file records the results of the full test suite run on the repository at the start of Phase 1.  It serves as a reference point for future changes; any deviation from this output should be investigated.

```
============================= test session starts =============================
platform win32 -- Python 3.11.13, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\shimp\OneDrive\Desktop\Fundamental_intelligence\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\shimp\OneDrive\Desktop\Fundamental_intelligence
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 48 items

tests/test_cleaner.py::test_zero_remains_zero PASSED                     [  2%]
tests/test_cleaner.py::test_missing_value_preserved PASSED               [  4%]
tests/test_cleaner.py::test_empty_file_is_rejected PASSED                [  6%]
tests/test_cleaner.py::test_validation_failure_blocks_db_load PASSED     [  8%]
tests/test_cleaner.py::test_partial_success_still_processed PASSED       [ 10%]
tests/test_cleaner.py::test_pipeline_failure_reporting PASSED            [ 12%]
tests/test_cleaner.py::test_failed_refresh_preserves_existing_silver_data PASSED [ 14%]
tests/test_cleaner.py::test_failed_publication_preserves_existing_silver_data PASSED [ 16%]
tests/test_cleaner.py::test_loader_rejects_incomplete_silver_dataset PASSED [ 18%]
tests/test_cleaner.py::test_duplicate_reporting_dates_are_rejected PASSED [ 20%]
tests/test_fetch_basics.py::test_fetch_succeeds_when_all_statements_are_available PASSED [ 22%]
tests/test_fetch_basics.py::test_fetch_fails_when_a_statement_is_empty PASSED [ 25%]
tests/test_fetch_basics.py::test_fetch_fails_when_a_statement_is_unavailable PASSED [ 27%]
tests/test_fetch_basics.py::test_fetch_fails_when_retrieval_raises_an_exception PASSED [ 29%]
tests/test_fetch_basics.py::test_fetch_fails_when_saving_a_statement_fails PASSED [ 31%]
tests/test_fetch_basics.py::test_failed_refresh_does_not_report_success_even_if_old_files_exist PASSED [ 33%]
tests/test_fetch_basics.py::test_successful_atomic_refresh_replaces_old_raw_files PASSED [ 35%]
tests/test_fetch_basics.py::test_publish_failure_preserves_existing_raw_data PASSED [ 37%]
tests/test_fetch_basics.py::test_download_batch_returns_failed_symbols PASSED [ 39%]
tests/test_loader.py::test_duplicate_observation_is_rejected PASSED      [ 41%]
tests/test_loader.py::test_different_metrics_are_allowed PASSED          [ 43%]
tests/test_loader.py::test_same_metric_for_different_dates_is_allowed PASSED [ 45%]
tests/test_loader.py::test_loading_same_data_twice_does_not_duplicate_rows PASSED [ 47%]
tests/test_loader.py::test_empty_required_statement_rolls_back_entire_load PASSED [ 50%]
tests/test_loader.py::test_all_missing_statement_rolls_back_entire_load PASSED [ 52%]
tests/test_loader.py::test_failure_in_last_statement_rolls_back_earlier_statements PASSED [ 54%]
tests/test_loader_data_quality.py::test_invalid_reporting_date_rolls_back_entire_load PASSED [ 56%]
tests/test_loader_data_quality.py::test_infinite_financial_value_rolls_back_entire_load[inf] PASSED [ 58%]
tests/test_loader_data_quality.py::test_infinite_financial_value_rolls_back_entire_load[-inf] PASSED [ 60%]
tests/test_loader_data_quality.py::test_duplicate_reporting_dates_are_rejected PASSED [ 62%]
tests/test_loader_data_quality.py::test_duplicate_metric_columns_are_rejected PASSED [ 64%]
tests/test_loader_data_quality.py::test_missing_financial_values_remain_allowed PASSED [ 66%]
tests/test_loader_data_quality.py::test_metric_headers_with_surrounding_whitespace_are_rejected PASSED [ 68%]
tests/test_loader_data_quality.py::test_blank_metric_header_is_rejected PASSED [ 70%]
tests/test_loader_data_quality.py::test_explicit_silver_dir_takes_precedence_over_environment PASSED [ 72%]
tests/test_pipeline.py::test_pipeline_success PASSED                     [ 75%]
tests/test_pipeline.py::test_failed_fetch_does_not_send_failed_ticker_downstream PASSED [ 77%]
tests/test_pipeline.py::test_all_fetches_fail PASSED                     [ 79%]
tests/test_pipeline.py::test_failed_cleaning_prevents_database_loading PASSED [ 81%]
tests/test_pipeline.py::test_unexpected_fetch_exception_is_reported PASSED [ 83%]
tests/test_pipeline.py::test_empty_ticker_list_returns_valid_report PASSED [ 85%]
tests/test_validator.py::test_all_valid_statements_pass PASSED           [ 87%]
tests/test_validator.py::test_missing_statement_is_reported PASSED       [ 89%]
tests/test_validator.py::test_empty_statement_fails PASSED               [ 91%]
tests/test_validator.py::test_missing_required_metric_fails PASSED       [ 93%]
tests/test_validator.py::test_non_numeric_revenue_fails PASSED           [ 95%]
tests/test_validator.py::test_missing_revenue_observation_is_allowed PASSED [ 97%]
tests/test_validator.py::test_unsupported_statement_fails PASSED         [100%]

============================= 48 passed in 4.76s =============================
```
