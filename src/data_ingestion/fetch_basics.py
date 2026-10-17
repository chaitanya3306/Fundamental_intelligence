import os
import logging
import pandas as pd
import yfinance as yf
from typing import List, Optional

# No market‑suffix helper – we now assume all tickers are plain US symbols.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class YFinanceFetcher:
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _save_dataframe(self, df: pd.DataFrame, symbol: str, statement_name: str):
        folder_path = os.path.join(self.data_dir, symbol)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{statement_name}.csv")
        try:
            df.to_csv(file_path)
            logger.info(f"file {file_path} created for {symbol}")
        except Exception as e:
            logger.error(f"Disk Error : could not save the {statement_name} of {symbol} : {e}")

    def fetch_company_data(self, symbol: str) -> bool:
        """Fetch financial statements for *symbol* using yfinance.

        In the US‑only version we pass the ticker to yfinance exactly as provided
        (no ``.NS`` suffix is added). This works for symbols such as ``AAPL`` or
        ``MSFT``.
        """
        try:
            yf_symbol = symbol  # US ticker – no suffix manipulation
            logger.info(f"Fetching data for ticker '{yf_symbol}' (original request: '{symbol}')")
            ticker = yf.Ticker(yf_symbol)

            statements = {
                "income_statement": ticker.financials,
                "balance_sheet": ticker.balance_sheet,
                "cashflow": ticker.cashflow,
            }

            for name, df in statements.items():
                if df is not None and not df.empty:
                    self._save_dataframe(df, symbol, name)
                else:
                    logger.warning(f"{name} for {symbol} is not fetched")
            return True
        except Exception as e:
            logger.error(f"API error : failed to fetch {symbol}: {e}")
            return False

    def download_batch(self, symbols: List[str]) -> List[str]:
        failed_symbols: List[str] = []
        for symbol in symbols:
            success = self.fetch_company_data(symbol)
            if not success:
                failed_symbols.append(symbol)
        return failed_symbols


if __name__ == "__main__":
    # Example US tickers – replace with any symbols you wish to download.
    COMPANIES = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

    fetcher = YFinanceFetcher()
    failures = fetcher.download_batch(COMPANIES)

    if not failures:
        logger.info("Success – all US data fetched!!")
    else:
        logger.warning(f"Completed with errors. Failed symbols: {failures}")
