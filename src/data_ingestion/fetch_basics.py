import logging
import os
import shutil
import tempfile
import uuid
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
        """Write one statement to the appropriate folder.

        If a staging directory is active (self._staging_dir is set), the file is written there.
        Otherwise it is written directly to the final raw‑data location.
        The method returns ``True`` on success and ``False`` on any ``OSError``.
        """
        # Determine the destination folder: staging if we are in a refresh, else the final raw folder.
        if getattr(self, "_staging_dir", None) is not None:
            # Staging directory already represents the target symbol folder.
            folder_path = self._staging_dir
        else:
            folder_path = self.data_dir / symbol
        file_path = folder_path / f"{statement_name}.csv"


        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(file_path)
            logger.info(
                "Saved %s for %s to %s",
                statement_name,
                symbol,
                file_path,
            )
            return True
        except OSError:
            logger.exception(
                "Could not save %s for %s to %s",
                statement_name,
                symbol,
                file_path,
            )
            return False

    def _publish_staged(self, symbol: str) -> bool:
        """Atomically replace the existing raw folder for *symbol* with the staged data.

        The method implements a safe publish:

        1. If a folder ``data_dir / symbol`` already exists, it is renamed to a
           temporary backup location.
        2. The staging folder (``self._staging_dir``) is then renamed to the target
           location.
        3. If any step fails, the method attempts to roll back by restoring the
           backup folder.  The return value indicates success (``True``) or a
           failure (``False``).
        """
        if not hasattr(self, "_staging_dir") or self._staging_dir is None:
            logger.error("No staging directory set for publishing %s", symbol)
            return False
        staging_path = self._staging_dir
        target_path = self.data_dir / symbol
        backup_path = self.data_dir / f".{symbol}_backup_{uuid.uuid4().hex}"
        try:
            # Preserve any existing raw data.
            if target_path.is_dir():
                os.replace(target_path, backup_path)
            # Atomically move the staged folder into place.
            os.replace(staging_path, target_path)
            # Publication succeeded – remove the backup.
            if backup_path.is_dir():
                shutil.rmtree(backup_path)
            return True
        except Exception as e:
            logger.exception(
                "Publication failed for %s; attempting rollback: %s", symbol, e
            )
            # Attempt to restore the original data if we have a backup.
            try:
                if backup_path.is_dir():
                    # Remove any partially moved target.
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    os.replace(backup_path, target_path)
            except Exception as rollback_err:
                logger.exception(
                    "Rollback failed for %s: %s", symbol, rollback_err
                )
            return False

    def fetch_company_data(self, symbol: str) -> bool:
        """Fetch and save all expected statements for a US ticker.

        This method now performs an *atomic* refresh:

        1. Retrieve the three statements via yfinance.
        2. Validate that none are missing or empty.
        3. Write the CSVs into a temporary staging directory.
        4. Verify the staged files exist.
        5. Publish the staged directory atomically, rolling back on any failure.

        Returns ``False`` if any step fails; ``True`` only when the new raw data
        has been successfully published.
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

        # Ensure all required statements are present and non‑empty.
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

        # Ensure the raw data directory exists before creating a staging sub‑directory.
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create a temporary staging directory inside the raw data root.
        try:
            staging_dir = tempfile.mkdtemp(
                dir=str(self.data_dir), prefix=f".{symbol}_staging_"
            )
            self._staging_dir = Path(staging_dir)
        except Exception:
            logger.exception("Failed to create staging directory for %s", symbol)
            return False

        # Write each statement to the staging folder using the existing helper.
        failed_writes = []
        for name, df in statements.items():
            if not self._save_dataframe(df, symbol, name):
                failed_writes.append(name)

        # Verify that all files were created in the staging area.
        if failed_writes:
            logger.error(
                "Incomplete refresh for %s; failed to save statements: %s",
                symbol,
                ", ".join(failed_writes),
            )
            shutil.rmtree(self._staging_dir, ignore_errors=True)
            self._staging_dir = None
            return False

        # At this point all staged files exist – attempt to publish them atomically.
        if not self._publish_staged(symbol):
            # Publication failed – clean up the staging directory before exiting.
            shutil.rmtree(self._staging_dir, ignore_errors=True)
            self._staging_dir = None
            return False


        # Success – clear the staging attribute.
        self._staging_dir = None
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
