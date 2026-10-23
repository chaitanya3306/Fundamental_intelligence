from unittest.mock import patch

from src.pipeline.run_pipeline import run_pipeline


@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_pipeline_success(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """Successful execution produces a complete report."""

    mock_fetcher_class.return_value.download_batch.return_value = []
    mock_cleaner_class.return_value.clean_batch.return_value = []
    mock_loader_class.return_value.load_batch.return_value = []

    result = run_pipeline(["AAPL", "MSFT"])

    assert result["status"] == "success"
    assert result["requested"] == ["AAPL", "MSFT"]
    assert result["fetch_failed"] == []
    assert result["clean_failed"] == []
    assert result["load_failed"] == []

    assert result["run_id"]
    assert result["started_at"]
    assert result["completed_at"]
    assert result["duration_seconds"] >= 0

    assert set(result["stage_durations_seconds"]) == {
        "fetch",
        "clean",
        "load",
    }

    mock_fetcher_class.return_value.download_batch.assert_called_once_with(
        ["AAPL", "MSFT"]
    )
    mock_cleaner_class.return_value.clean_batch.assert_called_once_with(
        ["AAPL", "MSFT"]
    )
    mock_loader_class.return_value.load_batch.assert_called_once_with(
        ["AAPL", "MSFT"]
    )


@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_failed_fetch_does_not_send_failed_ticker_downstream(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """Only successfully fetched tickers proceed to cleaning."""

    mock_fetcher_class.return_value.download_batch.return_value = ["AAPL"]
    mock_cleaner_class.return_value.clean_batch.return_value = []
    mock_loader_class.return_value.load_batch.return_value = []

    result = run_pipeline(["AAPL", "MSFT"])

    assert result["status"] == "partial_failure"
    assert result["fetch_failed"] == ["AAPL"]

    mock_cleaner_class.return_value.clean_batch.assert_called_once_with(
        ["MSFT"]
    )
    mock_loader_class.return_value.load_batch.assert_called_once_with(
        ["MSFT"]
    )



@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_all_fetches_fail(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """When every fetch fails, downstream stages receive no tickers."""

    mock_fetcher_class.return_value.download_batch.return_value = [
        "AAPL",
        "MSFT",
    ]
    mock_cleaner_class.return_value.clean_batch.return_value = []
    mock_loader_class.return_value.load_batch.return_value = []

    result = run_pipeline(["AAPL", "MSFT"])

    assert result["status"] == "failure"
    assert result["fetch_failed"] == ["AAPL", "MSFT"]
    assert result["clean_failed"] == []
    assert result["load_failed"] == []

    mock_cleaner_class.return_value.clean_batch.assert_called_once_with([])
    mock_loader_class.return_value.load_batch.assert_called_once_with([])





@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_failed_cleaning_prevents_database_loading(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """A ticker that fails cleaning must not reach the database loader."""

    mock_fetcher_class.return_value.download_batch.return_value = []
    mock_cleaner_class.return_value.clean_batch.return_value = ["AAPL"]
    mock_loader_class.return_value.load_batch.return_value = []

    result = run_pipeline(["AAPL", "MSFT"])

    assert result["status"] == "partial_failure"
    assert result["clean_failed"] == ["AAPL"]

    mock_loader_class.return_value.load_batch.assert_called_once_with(
        ["MSFT"]
    )


@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_unexpected_fetch_exception_is_reported(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """An unexpected fetch exception is logged and reported as a failure."""

    mock_fetcher_class.return_value.download_batch.side_effect = RuntimeError(
        "Provider unavailable"
    )

    result = run_pipeline(["AAPL", "MSFT"])

    assert result["status"] == "failure"
    assert result["fetch_failed"] == ["AAPL", "MSFT"]

    mock_cleaner_class.return_value.clean_batch.assert_called_once_with([])
    mock_loader_class.return_value.load_batch.assert_called_once_with([])


def test_empty_ticker_list_returns_valid_report():
    """An empty request produces a valid report without running stages."""

    with (
        patch("src.pipeline.run_pipeline.YFinanceFetcher") as fetcher,
        patch("src.pipeline.run_pipeline.FinancialCleaner") as cleaner,
        patch("src.pipeline.run_pipeline.DatabaseLoader") as loader,
    ):
        result = run_pipeline([])

    assert result["status"] == "success"
    assert result["requested"] == []
    assert result["run_id"]
    assert result["completed_at"]
    assert result["duration_seconds"] >= 0

    fetcher.assert_not_called()
    cleaner.assert_not_called()
    loader.assert_not_called()