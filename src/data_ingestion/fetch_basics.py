import logging
import os
from pathlib import Path
from typing import List

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    # Provide a stub yfinance with a Ticker class for tests that mock it.
    class _YFinanceStub:
        class Ticker:
            def __init__(self, *args, **kwargs):
                raise ImportError("yfinance package is required for YFinanceFetcher")
    yf = _YFinanceStub()

logger = logging.getLogger(__name__)


class YFinanceFetcher:
    """Fetch annual financial statements into the raw-data layer.

    A ticker is reported as successful only when all three expected statements
    are retrieved and written. Missing statements are not treated as success.
    """

    STATEMENTS = {
        "income_statement": "financials",
        "balance_sheet": "balance_sheet",
        "cashflow": "cashflow",
    }

    def __init__(self, data_dir: str = "data/raw") -> None:
        self.data_dir = Path(data_dir)

    def _save_dataframe(
        self, df: pd.DataFrame, symbol: str, statement_name: str
    ) -> bool:
        """Write one statement and return whether the write succeeded."""
        folder_path = self.data_dir / symbol
        file_path = folder_path / f"{statement_name}.csv"

        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(file_path)
            logger.info("Saved %s for %s to %s", statement_name, symbol, file_path)
            return True
        except OSError:
            logger.exception(
                "Could not save %s for %s to %s",
                statement_name,
                symbol,
                file_path,
            )
            return False

    def fetch_company_data(self, symbol: str) -> bool:
        """Fetch and save all expected statements for a US ticker.

        Returns False if retrieval or writing fails for any expected statement.
        A failed refresh may leave older files on disk; callers must therefore
        use this result to prevent downstream processing of this ticker.
        """
        try:
            logger.info("Fetching financial statements for US ticker %s", symbol)
            ticker = yf.Ticker(symbol)
            statements = {
                "income_statement": ticker.financials,
                "balance_sheet": ticker.balance_sheet,
                "cashflow": ticker.cashflow,
            }
        except Exception:
            logger.exception("Failed to retrieve statements for %s", symbol)
            return False

        missing = [
            name
            for name, df in statements.items()
            if df is None or not isinstance(df, pd.DataFrame) or df.empty
        ]
        if missing:
            logger.warning(
                "Incomplete refresh for %s; unavailable statements: %s",
                symbol,
                ", ".join(missing),
            )
            return False

        failed_writes = []
        for name, df in statements.items():
            if not self._save_dataframe(df, symbol, name):
                failed_writes.append(name)

        if failed_writes:
            logger.error(
                "Incomplete refresh for %s; failed to save statements: %s",
                symbol,
                ", ".join(failed_writes),
            )
            return False

        return True

    def download_batch(self, symbols: List[str]) -> List[str]:
        """Return tickers for which the complete refresh failed."""
        failed_symbols: List[str] = []
        for symbol in symbols:
            if not self.fetch_company_data(symbol):
                failed_symbols.append(symbol)
        return failed_symbols


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    companies = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    failures = YFinanceFetcher().download_batch(companies)

    if failures:
        logger.warning("Financial statement fetch failed for: %s", failures)
    else:
        logger.info("All requested financial statements were fetched and saved.")
