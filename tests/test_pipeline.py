
from unittest.mock import MagicMock, patch

from src.pipeline.run_pipeline import run_pipeline


@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_pipeline_success(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """All tickers succeed at every pipeline stage."""

    mock_fetcher = mock_fetcher_class.return_value
    mock_cleaner = mock_cleaner_class.return_value
    mock_loader = mock_loader_class.return_value

    mock_fetcher.download_batch.return_value = []
    mock_cleaner.clean_batch.return_value = []
    mock_loader.load_batch.return_value = []

    result = run_pipeline(["AAPL", "MSFT"])

    assert result["requested"] == ["AAPL", "MSFT"]
    assert result["fetch_failed"] == []
    assert result["clean_failed"] == []
    assert result["load_failed"] == []

    mock_fetcher.download_batch.assert_called_once_with(["AAPL", "MSFT"])
    mock_cleaner.clean_batch.assert_called_once_with(["AAPL", "MSFT"])
    mock_loader.load_batch.assert_called_once_with(["AAPL", "MSFT"])


@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_failed_fetch_skips_cleaning_and_loading(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """A ticker that fails ingestion must not reach later stages."""

    mock_fetcher = mock_fetcher_class.return_value
    mock_cleaner = mock_cleaner_class.return_value
    mock_loader = mock_loader_class.return_value

    mock_fetcher.download_batch.return_value = ["AAPL"]
    mock_cleaner.clean_batch.return_value = []
    mock_loader.load_batch.return_value = []

    result = run_pipeline(["AAPL"])

    assert result["fetch_failed"] == ["AAPL"]

    mock_cleaner.clean_batch.assert_called_once_with([])
    mock_loader.load_batch.assert_called_once_with([])


@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_successful_ticker_continues_when_another_fetch_fails(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """A failed ticker must not prevent other tickers from being processed."""

    mock_fetcher = mock_fetcher_class.return_value
    mock_cleaner = mock_cleaner_class.return_value
    mock_loader = mock_loader_class.return_value

    mock_fetcher.download_batch.return_value = ["AAPL"]
    mock_cleaner.clean_batch.return_value = []
    mock_loader.load_batch.return_value = []

    result = run_pipeline(["AAPL", "MSFT"])

    assert result["fetch_failed"] == ["AAPL"]

    mock_cleaner.clean_batch.assert_called_once_with(["MSFT"])
    mock_loader.load_batch.assert_called_once_with(["MSFT"])


@patch("src.pipeline.run_pipeline.DatabaseLoader")
@patch("src.pipeline.run_pipeline.FinancialCleaner")
@patch("src.pipeline.run_pipeline.YFinanceFetcher")
def test_all_failed_tickers_never_reach_cleaning_or_loading(
    mock_fetcher_class,
    mock_cleaner_class,
    mock_loader_class,
):
    """If every fetch fails, no ticker should reach downstream processing."""

    mock_fetcher = mock_fetcher_class.return_value
    mock_cleaner = mock_cleaner_class.return_value
    mock_loader = mock_loader_class.return_value

    mock_fetcher.download_batch.return_value = ["AAPL", "MSFT"]
    mock_cleaner.clean_batch.return_value = []
    mock_loader.load_batch.return_value = []

    result = run_pipeline(["AAPL", "MSFT"])

    assert result["fetch_failed"] == ["AAPL", "MSFT"]
    assert result["clean_failed"] == []
    assert result["load_failed"] == []

    mock_cleaner.clean_batch.assert_called_once_with([])
    mock_loader.load_batch.assert_called_once_with([])
