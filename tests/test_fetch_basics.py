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

# ----------------------------------------------------------------------
# New tests for atomic publish behavior
# ----------------------------------------------------------------------

@patch("src.data_ingestion.fetch_basics.yf.Ticker")
def test_successful_atomic_refresh_replaces_old_raw_files(
    mock_ticker_factory, fetcher, mock_ticker, tmp_path
):
    """When the refresh succeeds, the new files replace any existing raw data atomically."""
    mock_ticker_factory.return_value = mock_ticker

    # Create an existing raw folder with old content.
    symbol = "AAPL"
    old_dir = fetcher.data_dir / symbol
    old_dir.mkdir(parents=True)
    (old_dir / "income_statement.csv").write_text("old_income", encoding="utf-8")
    (old_dir / "balance_sheet.csv").write_text("old_balance", encoding="utf-8")
    (old_dir / "cashflow.csv").write_text("old_cash", encoding="utf-8")

    result = fetcher.fetch_company_data(symbol)

    assert result is True
    # The directory should still exist under the same path.
    new_dir = fetcher.data_dir / symbol
    assert new_dir.is_dir()
    # Verify that each file now contains the fresh data (i.e., not the old placeholder).
    assert "old_income" not in (new_dir / "income_statement.csv").read_text()
    assert "old_balance" not in (new_dir / "balance_sheet.csv").read_text()
    assert "old_cash" not in (new_dir / "cashflow.csv").read_text()

@patch("src.data_ingestion.fetch_basics.yf.Ticker")
def test_publish_failure_preserves_existing_raw_data(
    mock_ticker_factory, fetcher, mock_ticker, tmp_path
):
    """If publishing the staged data fails, the original raw files remain unchanged."""
    mock_ticker_factory.return_value = mock_ticker

    symbol = "AAPL"
    old_dir = fetcher.data_dir / symbol
    old_dir.mkdir(parents=True)
    old_income = old_dir / "income_statement.csv"
    old_income.write_text("old_income", encoding="utf-8")
    old_balance = old_dir / "balance_sheet.csv"
    old_balance.write_text("old_balance", encoding="utf-8")
    old_cash = old_dir / "cashflow.csv"
    old_cash.write_text("old_cash", encoding="utf-8")

    # Patch the publish step to simulate a failure after staging.
    with patch.object(fetcher, "_publish_staged", return_value=False):
        result = fetcher.fetch_company_data(symbol)

    assert result is False
    # The original files must be intact.
    assert old_income.read_text() == "old_income"
    assert old_balance.read_text() == "old_balance"
    assert old_cash.read_text() == "old_cash"

    # No new folder should have been left behind.
    assert not any(p.name.startswith("." + symbol + "_staging_") for p in fetcher.data_dir.iterdir())


def test_download_batch_returns_failed_symbols(fetcher, mock_ticker, mock_ticker_factory):
    # Use the patched fetcher to simulate mixed success/failure.
    mock_ticker_factory.return_value = mock_ticker
    # For simplicity, let fetcher succeed for AAPL and fail for MSFT.
    with patch.object(fetcher, "fetch_company_data", side_effect=[True, False]):
        failures = fetcher.download_batch(["AAPL", "MSFT"])
    assert failures == ["MSFT"]
