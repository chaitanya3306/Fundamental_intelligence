import pandas as pd
import os
import logging

from typing import List
from src.data_validation.validator import FinancialValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FinancialCleaner:
    def __init__(self,raw_dir:str="data/raw",silver_dir:str="data/silver"):
        self.raw_dir=raw_dir
        self.silver_dir=silver_dir
        os.makedirs(silver_dir, exist_ok=True)
        # Expose silver directory via environment for downstream components (e.g., DatabaseLoader)
        os.environ["FINANCIAL_SILVER_DIR"] = self.silver_dir
        self.validator=FinancialValidator()

    def _transpose_and_clean(self,df:pd.DataFrame)->pd.DataFrame:
        """Return the DataFrame unchanged while preserving true missing values.

        The original CSV format uses metric rows and date columns. The cleaning
        step should therefore keep that orientation and avoid filling NaNs.
        """
        # No transposition or filling of missing values – we simply return the
        # DataFrame as‑is so downstream processing (validation, loading) sees the
        # raw metric‑by‑date layout.
        return df

    def process_company(self, symbol: str) -> bool:
        """Process all statements for a given ticker.

        Returns True if at least one statement was successfully cleaned and
        stored in the silver layer, otherwise False.
        """
        try:
            logger.info(f"processing {symbol}")

            statements = ["income_statement", "balance_sheet", "cashflow"]

            raw_folder = os.path.join(self.raw_dir, symbol)
            failed_paths = self.validator.validate_data_folder(raw_folder)

            if failed_paths:
                for fp in failed_paths:
                    logger.warning(f"validation failed for {fp} skipping this statement")

            company_silver_dir = os.path.join(self.silver_dir, symbol)
            os.makedirs(company_silver_dir, exist_ok=True)

            any_success = False
            for stm in statements:
                file_path = os.path.join(self.raw_dir, symbol, f"{stm}.csv")

                if not os.path.exists(file_path):
                    logger.warning(f"file not found : {file_path}")
                    continue

                if file_path in failed_paths:
                    continue

                df_raw = pd.read_csv(file_path, index_col=0)
                df_clean = self._transpose_and_clean(df_raw)

                save_path = os.path.join(company_silver_dir, f"{stm}.csv")
                df_clean.to_csv(save_path)
                any_success = True

            if not any_success:
                logger.warning(f"No valid statements processed for {symbol}")
                return False

            return True
        except Exception as e:
            logger.error(f"symbol not found or error in it : {symbol} : {e}")
            return False

    def clean_batch(self,company_list:List[str])->List[str]:
        failed=[]
        for symbol in company_list:
            if not self.process_company(symbol):
                failed.append(symbol)
        return failed


if __name__=="__main__":
    COMPANIES = ['AAPL','MSFT']
    cleaner=FinancialCleaner()

    failed=cleaner.clean_batch(COMPANIES)

    if failed:
        logger.warning(f"cleaning  failed for  {failed}")
    logger.info("All companies Cleaned Successfully")








