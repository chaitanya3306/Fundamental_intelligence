import pandas as pd
import os
import logging

from typing import List


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FinancialCleaner:
    def __init__(self,raw_dir:str="data/raw",silver_dir:str="data/silver"):
        self.raw_dir=raw_dir
        self.silver_dir=silver_dir
        os.makedirs(silver_dir)

    def _transpose_and_clean(self,df:pd.DataFrame)->pd.DataFrame:
        #in this we just transpose and clean the missing values
        df=df.T

        df.index=pd.to_datetime(df.index)
        df.index.name='date'

        df=df.fillna(0.0)

        return df

    def process_company(self,symbol:str)->bool:
        try:
            logger.info(f"processing {symbol}")

            statements=["income_statement","balance_sheet","cashflow"]

            company_silver_dir=os.path.join(self.silver_dir,symbol)
            os.makedirs(company_silver_dir)
            for stm in statements:
                file_path=os.path.join(self.raw_dir,symbol,f"{stm}.csv")

                if not os.path.exists(file_path):
                    logger.warning(f"file not found : {file_path}")

                df_raw=pd.read_csv(file_path,index_col=0)
                df_clean=self._transpose_and_clean(df_raw)

                save_path=os.path.join(company_silver_dir,f"{stm}.csv")
                df_clean.to_csv(save_path)

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
    COMPANIES = ['TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'RELIANCE.NS']
    cleaner=FinancialCleaner()

    failed=cleaner.clean_batch(COMPANIES)

    if failed:
        logger.warning(f"cleaning  failed for  {failed}")
    logger.info("All companies Cleaned Successfully")








