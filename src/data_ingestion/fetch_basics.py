import yfinance as yf
import os
import pandas as pd
import logging
from typing import List,Optional


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YFinanceFetcher:
    def __init__(self,data_dir:str="data/raw"):
        self.data_dir=data_dir
        os.makedirs(self.data_dir,exist_ok=True)

    def _save_dataframe(self,df:pd.DataFrame,symbol:str,statement_name:str):
        folder_path=os.path.join(self.data_dir,symbol)
        os.makedirs(folder_path,exist_ok=True)

        #now create the filepath in that folder
        file_path=os.path.join(folder_path,f"{statement_name}.csv")

        try:
            df.to_csv(file_path)
            logger.info(f"file {file_path} created for {symbol}")
        except Exception as e:
            logger.error(
                f"Disk Error : could not save the {statement_name} of {symbol} : {e}"
            )

    def fetch_company_data(self,symbol):
        try:
            logger.info(f"fetching for {symbol}")
            ticker=yf.Ticker(symbol)

            statemets={
                "income_statement":ticker.financials,
                "balance_sheet":ticker.balance_sheet,
                "cashflow":ticker.cashflow
            }

            for name,df in statemets.items():
                if df is not None and not df.empty:
                    self._save_dataframe(df,symbol,name)
                else:
                    logger.warning(f"{name} for {symbol} is not fetched")
            return True

        except Exception as e:
            logger.error(f"API error : failed to fetch {symbol}:{e}")
            return False

    def download_batch(self,symbols:List[str])->List[str]:
        failed_symbols=[]
        for symbol in symbols:
            success=self.fetch_company_data(symbol)
            if not success:
                failed_symbols.append(symbol)
        return failed_symbols


if __name__=="__main__":
    COMPANIES = ['TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'RELIANCE.NS', 'TATAMOTORS.NS']

    fetcher=YFinanceFetcher()
    failuers=fetcher.download_batch(COMPANIES)

    if not failuers:
        logger.info("Success ALL data Fetched !!")
    else:
        logger.warning(f"Completed with errors . Failed symbols : {failuers}")












































