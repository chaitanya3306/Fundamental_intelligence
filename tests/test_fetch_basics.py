from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.data_ingestion.fetch_basics import YFinanceFetcher


@pytest.fixture
def fetcher(tmp_path):
    """Create a fetcher that writes only inside pytest's temporary directory."""
    return YFinanceFetcher(data_dir=str(tmp_path / "raw"))


@pytest.fixture
def mock_ticker():
    """Create a fake company with all three financial statements."""
    ticker = MagicMock()

    ticker.financials = pd.DataFrame(
        {"2024-12-31": [1000]},
        index=["Total Revenue"],
    )

    ticker.balance_sheet = pd.DataFrame(
        {"2024-12-31": [500]},
        index=["Total Assets"],
    )

    ticker.cashflow = pd.DataFrame(
        {"2024-12-31": [200]},
        index=["Operating Cash Flow"],
    )

    return ticker


@patch("src.data_ingestion.fetch_basics.yf.Ticker")
def test_fetch_succeeds_when_all_statements_are_available(
    mock_ticker_factory, fetcher, mock_ticker
):
    """All three statements are available and saved successfully."""
    mock_ticker_factory.return_value = mock_ticker

    result = fetcher.fetch_company_data("AAPL")

    assert result is True

    company_dir = fetcher.data_dir / "AAPL"

    assert (company_dir / "income_statement.csv").exists()
    assert (company_dir / "balance_sheet.csv").exists()
    assert (company_dir / "cashflow.csv").exists()

    mock_ticker_factory.assert_called_once_with("AAPL")


@patch("src.data_ingestion.fetch_basics.yf.Ticker")
def test_fetch_fails_when_a_statement_is_empty(
    mock_ticker_factory, fetcher, mock_ticker
):
    """An empty statement must not be treated as a successful refresh."""
    mock_ticker.balance_sheet = pd.DataFrame()
    mock_ticker_factory.return_value = mock_ticker

    result = fetcher.fetch_company_data("AAPL")

    assert result is False


@patch("src.data_ingestion.fetch_basics.yf.Ticker")
def test_fetch_fails_when_a_statement_is_unavailable(
    mock_ticker_factory, fetcher, mock_ticker
):
    """A missing statement must cause the refresh to fail."""
    mock_ticker.balance_sheet = None
    mock_ticker_factory.return_value = mock_ticker

    result = fetcher.fetch_company_data("AAPL")

    assert result is False


@patch("src.data_ingestion.fetch_basics.yf.Ticker")
def test_fetch_fails_when_retrieval_raises_an_exception(
    mock_ticker_factory,
):
    """A provider exception must be reported as a failed fetch."""
    mock_ticker_factory.side_effect = RuntimeError("Provider unavailable")

    fetcher = YFinanceFetcher(data_dir="unused-test-data")

    result = fetcher.fetch_company_data("AAPL")

    assert result is False


@patch("src.data_ingestion.fetch_basics.yf.Ticker")
def test_fetch_fails_when_saving_a_statement_fails(
    mock_ticker_factory, fetcher, mock_ticker
):
    """A failed file write must cause the refresh to fail."""
    mock_ticker_factory.return_value = mock_ticker

    with patch.object(
        fetcher,
        "_save_dataframe",
        side_effect=[True, False, True],
    ):
        result = fetcher.fetch_company_data("AAPL")

    assert result is False


@patch("src.data_ingestion.fetch_basics.yf.Ticker")
def test_failed_refresh_does_not_report_success_even_if_old_files_exist(
    mock_ticker_factory, fetcher, mock_ticker
):
    """Old files must not turn an unsuccessful refresh into a success."""
    mock_ticker_factory.return_value = mock_ticker

    company_dir = fetcher.data_dir / "AAPL"
    company_dir.mkdir(parents=True)

    old_file = company_dir / "balance_sheet.csv"
    old_file.write_text("old financial data", encoding="utf-8")

    mock_ticker.balance_sheet = pd.DataFrame()

    result = fetcher.fetch_company_data("AAPL")

    assert result is False
    assert old_file.exists()
