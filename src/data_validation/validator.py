
import pandas as pd
import logging
import os
from typing import List,Tuple


import numpy as np

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

    def _check_reporting_periods(self,df:pd.DataFrame)->Tuple[bool,str]:
    #     in this we are checking is the reporting periods are empty or duplicaetd or no
        reporting_periods=pd.Index(df.columns)
        parsed_periods = pd.to_datetime(
            reporting_periods,
            errors="coerce",
        )

        invalid_periods = parsed_periods.isna()

        if invalid_periods.any():
            bad_periods = reporting_periods[invalid_periods].tolist()

            return False, f"Invalid reporting periods found: {bad_periods}"

        if parsed_periods.duplicated().any():
            duplicate_periods = parsed_periods[
                parsed_periods.duplicated(keep=False)
            ].tolist()

            return False, (
                f"Duplicate reporting periods found: {duplicate_periods}"
            )

        return True, ""



    def _check_columns(self,df:pd.DataFrame,statement:str)->Tuple[bool,str]:
        if statement not in self.required_columns:
            return False, f"Unsupported statement type: {statement}"

        required_cols=self.required_columns.get(statement,[])
        all_available_labels=list(df.index)+list(df.columns)
        missing=[col for col in required_cols if col not in all_available_labels]

        if missing:
            return False , f"some features are missing : {missing}"
        return True,""

    def _check_numeric_values(
            self,
            df: pd.DataFrame,
            statement: str,
    ) -> Tuple[bool, str]:

        required_cols = self.required_columns[statement]

        for metric in required_cols:
            if metric in df.index:
                values = df.loc[metric]
            elif metric in df.columns:
                values = df[metric]
            else:
                return False, f"Required metric not found: {metric}"

            numeric_values = pd.to_numeric(values, errors="coerce")

            invalid_values = values.notna() & numeric_values.isna()

            if invalid_values.any():
                bad_values = values[invalid_values].tolist()

                return False, (
                    f"Non-numeric values found for {metric}: {bad_values}"
                )

        return True, ""

    def _check_metric_names(
            self,
            df: pd.DataFrame,
    ) -> Tuple[bool, str]:

        metric_names = df.index.astype(str).str.strip()

        blank_names = metric_names == ""

        if blank_names.any():
            return False, "Blank financial metric names found"

        duplicate_names = metric_names[
            metric_names.duplicated(keep=False)
        ].unique().tolist()

        if duplicate_names:
            return False, (
                f"Duplicate financial metric names found: {duplicate_names}"
            )

        return True, ""

    def _check_infinite_values(
            self,
            df: pd.DataFrame,
    ) -> Tuple[bool, str]:

        numeric_df = df.apply(
            pd.to_numeric,
            errors="coerce",
        )

        infinite_mask = np.isinf(numeric_df)

        if infinite_mask.any().any():
            infinite_locations = np.where(infinite_mask)

            return False, (
                f"Infinite values found at positions: "
                f"{list(zip(infinite_locations[0], infinite_locations[1]))}"
            )

        return True, ""

    def _check_structure(
            self,
            df: pd.DataFrame,
    ) -> Tuple[bool, str]:

        if df.index.isna().any():
            return False, "Missing financial metric names found"

        if len(df.index) == 0:
            return False, "No financial metrics found"

        if len(df.columns) == 0:
            return False, "No reporting periods found"

        if df.columns.isna().any():
            return False, "Missing reporting period columns found"

        return True, ""

    def validate_file(self,file_path:str,statement:str)->bool:
        #in this file we are checking all the constraints together on any file
        try:
            df=pd.read_csv(file_path,index_col=0)

            #first check empty check
            is_ok,msg=self._check_empty(df)
            if not is_ok:
                logger.warning(f"validation failed empty file detected : {file_path}:{msg}")
                return False

            is_ok, msg = self._check_reporting_periods(df)

            if not is_ok:
                logger.warning(
                    "Validation failed for %s: %s",
                    file_path,
                    msg,
                )
                return False


            is_ok, msg = self._check_metric_names(df)

            if not is_ok:
                logger.warning(
                    "Validation failed for %s: %s",
                    file_path,
                    msg,
                )
                return False

            is_ok, msg = self._check_structure(df)

            if not is_ok:
                logger.warning(
                    "Validation failed for %s: %s",
                    file_path,
                    msg,
                )
                return False


            is_ok,msg=self._check_columns(df,statement)
            if not is_ok :
                logger.warning(f"validation failed missing features detected :{file_path} : {msg}")
                return False



            is_ok, msg = self._check_numeric_values(df, statement)
            if not is_ok:
                logger.warning(
                    "Validation failed for %s: %s",
                    file_path,
                    msg,
                )
                return False

            is_ok, msg = self._check_infinite_values(df)
            if not is_ok:
                logger.warning(
                    "Validation failed for %s: %s",
                    file_path,
                    msg,
                )
                return False

            logger.info(f"{file_path} successfully validated !")
            return True

        except Exception:

            logger.exception("Failed to validate file: %s", file_path)
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
                failed_files.append(file_path)

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







