"""Test fixtures shared across the test suite."""
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_ticker_factory():
    """Patch the yfinance Ticker class and expose the mock factory.

    The test can set ``mock_ticker_factory.return_value`` to a MagicMock
    that provides ``financials``, ``balance_sheet`` and ``cashflow`` data.
    """
    with patch("src.data_ingestion.fetch_basics.yf.Ticker") as mock_factory:
        yield mock_factory
