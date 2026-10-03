
import pandas as pd
import logging
import os
from typing import List,Tuple




logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialValidator:
    def __init__(self):
        self.required_columns = {
            "income_statement": ["Total Revenue"],
            "balance_sheet": ["Total Assets", "Total Liabilities Net Minority Interest"],
            "cashflow": ["Free Cash Flow"] # Changed from 'Net Income' to 'Free Cash Flow'
        }

    def _check_empty(self,df:pd.DataFrame)->Tuple[bool,str]:
        if df.empty:
            return False,"File is Empty"
        return True,""

    def _check_columns(self,df:pd.DataFrame,statement:str)->Tuple[bool,str]:
        required_cols=self.required_columns.get(statement,[])
        all_available_labels=list(df.index)+list(df.columns)
        missing=[col for col in required_cols if col not in all_available_labels]

        if missing:
            return False , f"some features are missing : {missing}"
        return True,""

    def validate_file(self,file_path:str,statement:str)->bool:
        #in this file we are checking all the constraints together on any file
        try:
            df=pd.read_csv(file_path,index_col=0)

            #first check empty check
            is_ok,msg=self._check_empty(df)
            if not is_ok:
                logger.warning(f"validation failed empty file detected : {file_path}:{msg}")
                return False

            is_ok,msg=self._check_columns(df,statement)
            if not is_ok :
                logger.warning(f"validation failed missing features detected :{file_path} : {msg}")
                return False

            logger.info(f"{file_path} successfully validated !")
            return True

        except Exception as e:
            logger.error(f"failed validate file {file_path}")
            return False

    def validate_data_folder(self,folder_path:str):
        #in this we are checking whole folder using the previous methods
        failed_files=[]
        for statement in ['income_statement','balance_sheet','cashflow']:
            file_path=os.path.join(folder_path,f"{statement}.csv")
            if os.path.exists(file_path):
                if not self.validate_file(file_path,statement):
                    failed_files.append(file_path)
            else:
                logger.error(f"missing file {file_path}")

        return failed_files


if __name__=="__main__":
    base_folder_path=os.path.join("data","raw")
    COMPANIES = ['TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'RELIANCE.NS']
    validator=FinancialValidator()

    all_failures={}

    for symbol in COMPANIES:
        folder_path=os.path.join(base_folder_path,symbol)

        failure=validator.validate_data_folder(folder_path)

        if failure:
            all_failures[symbol]=failure

    if all_failures:
        logger.warning(f"Validation failed for the this {all_failures}")
    else:
        logger.info("ALl companies passed Validation !")







