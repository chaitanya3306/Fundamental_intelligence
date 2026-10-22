"""Validate and normalize raw financial statements into the Silver layer."""
import logging
import os
from pathlib import Path
from typing import List
import shutil
import tempfile
import pandas as pd

from src.data_validation.validator import FinancialValidator

logger = logging.getLogger(__name__)

STATEMENTS = ("income_statement", "balance_sheet", "cashflow")


class FinancialCleaner:
    def __init__(self, raw_dir: str = "data/raw", silver_dir: str = "data/silver"):
        self.raw_dir = Path(raw_dir)
        self.silver_dir = Path(silver_dir)
        self.silver_dir.mkdir(parents=True, exist_ok=True)
        # DatabaseLoader uses this setting to locate this instance's Silver layer.
        os.environ["FINANCIAL_SILVER_DIR"] = str(self.silver_dir)
        self.validator = FinancialValidator()

    def _transpose_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert provider layout (metric rows, period columns) to period rows.

        Missing values are intentionally preserved as NaN: absence of a reported
        value is not the same thing as a financial value of zero.
        """
        result = df.transpose().copy()
        result.index = pd.to_datetime(result.index, errors="raise").date
        result.index.name = "date"
        result.columns = result.columns.astype(str).str.strip()
        for column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="raise")
        return result



    def process_company(self, symbol: str) -> bool:
        """Clean all statements before publishing them to the Silver layer."""
        raw_folder = self.raw_dir / symbol
        silver_folder = self.silver_dir / symbol

        try:
            if not raw_folder.is_dir():
                logger.error(
                    "Raw data folder does not exist for %s: %s",
                    symbol,
                    raw_folder,
                )
                return False

            # Validate all required raw statements.
            invalid_paths = set(
                self.validator.validate_data_folder(str(raw_folder))
            )

            # Build all cleaned files in a temporary directory first.
            with tempfile.TemporaryDirectory(
                    dir=str(self.silver_dir),
                    prefix=f".{symbol}_staging_",
            ) as staging_dir:
                staging_folder = Path(staging_dir)
                successful = set()

                for statement in STATEMENTS:
                    source = raw_folder / f"{statement}.csv"
                    destination = staging_folder / f"{statement}.csv"

                    if not source.is_file():
                        logger.warning(
                            "Missing raw statement for %s: %s",
                            symbol,
                            source,
                        )
                        continue

                    if str(source) in invalid_paths:
                        logger.warning(
                            "Skipping invalid statement for %s: %s",
                            symbol,
                            source,
                        )
                        continue

                    try:
                        raw_df = pd.read_csv(source, index_col=0)
                        cleaned = self._transpose_and_clean(raw_df)

                        if cleaned.empty:
                            logger.warning(
                                "Skipping empty cleaned statement for %s: %s",
                                symbol,
                                source,
                            )
                            continue

                        cleaned.to_csv(destination, index=True)
                        successful.add(statement)

                    except (
                            OSError,
                            ValueError,
                            TypeError,
                            pd.errors.ParserError,
                    ):
                        logger.exception(
                            "Could not clean %s statement for %s",
                            statement,
                            symbol,
                        )

                # Do not publish partial results.
                if successful != set(STATEMENTS):
                    logger.error(
                        "Cleaning incomplete for %s. Successfully cleaned: %s",
                        symbol,
                        successful,
                    )
                    return False

                # All three statements are ready.
                # Publish them only after cleaning has succeeded.
                silver_folder.mkdir(parents=True, exist_ok=True)

                for statement in STATEMENTS:
                    staged_file = staging_folder / f"{statement}.csv"
                    destination = silver_folder / f"{statement}.csv"
                    temporary_destination = destination.with_suffix(".csv.tmp")

                    try:
                        shutil.copy2(staged_file, temporary_destination)
                        os.replace(temporary_destination, destination)
                    finally:
                        temporary_destination.unlink(missing_ok=True)

            logger.info("Successfully cleaned all statements for %s", symbol)
            return True

        except Exception:
            logger.exception("Unexpected cleaning error for %s", symbol)
            return False



    def clean_batch(self, company_list: List[str]) -> List[str]:
        return [symbol for symbol in company_list if not self.process_company(symbol)]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    failures = FinancialCleaner().clean_batch(["AAPL", "MSFT"])
    if failures:
        logger.error("Cleaning failed for: %s", failures)
    else:
        logger.info("All requested companies cleaned.")
