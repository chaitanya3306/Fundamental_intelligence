
import pandas as pd
import logging
import os
from typing import List
from datetime import datetime



from .session import db_manager
from .models import Company, FinancialStatement

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


from types import SimpleNamespace


class DatabaseLoader:

    # Expose model classes for tests that expect DatabaseLoader.model
    model = SimpleNamespace(Company=Company, FinancialStatement=FinancialStatement)

    def __init__(self,silver_dir:str="data/silver"):
        # Allow overriding the silver directory via an environment variable for
        # testing or pipeline integration. If the env var is set, it takes
        # precedence over the default argument.
        env_dir = os.getenv("FINANCIAL_SILVER_DIR")
        self.silver_dir = env_dir if env_dir is not None else silver_dir


    def _get_or_create_company(self,session,symbol:str)->int:
        company=session.query(Company).filter(Company.ticker==symbol).first()
        if not company:
            logger.info(f"adding {symbol} company")
            company=Company(ticker=symbol)
            session.add(company)
            session.flush()

        return company.company_id



    def _upsert_statement(self, session, company_id: int, statement_type: str, report_date, metric_name: str, value: float):
        """
        The Upsert Logic: Check if record exists.
        If yes -> Update. If no -> Insert.
        """
        # Search for an existing record with the same company, date, statement, and metric
        existing_entry = session.query(FinancialStatement).filter(
            FinancialStatement.company_id == company_id,
            FinancialStatement.date == report_date,
            FinancialStatement.statement_type == statement_type,
            FinancialStatement.metric_name == metric_name
        ).first()

        if existing_entry:
            # UPDATE existing record
            existing_entry.value = value
        else:
            # INSERT new record
            entry = FinancialStatement(
                company_id=company_id,
                date=report_date,
                statement_type=statement_type,
                metric_name=metric_name,
                value=value
            )
            session.add(entry)






    def _load_statement(self,session,df:pd.DataFrame,company_id:int,statement_type:str):
        # Determine orientation: if index values are dates (parsable), treat rows as dates;
        # otherwise assume index contains metric names and columns are dates.
        if pd.api.types.is_string_dtype(df.index):
            # Index likely metric names
            for metric_name, row in df.iterrows():
                for date_str, value in row.items():
                    if pd.isna(value):
                        continue
                    report_date = pd.to_datetime(date_str).date()
                    self._upsert_statement(session, company_id, statement_type, report_date,
                                           metric_name, float(value))
        else:
            # Index likely dates
            for date, row in df.iterrows():
                report_date = pd.to_datetime(date).date()
                for metric_name, value in row.items():
                    if pd.isna(value):
                        continue
                    self._upsert_statement(session, company_id, statement_type, report_date,
                                           metric_name, float(value))
    def _load_company_data(self,symbol):
        #handle the company
        session=db_manager.get_session()
        try:
            company_id=self._get_or_create_company(session,symbol)

            statements = ["income_statement", "balance_sheet", "cashflow"]

            for stm in statements:
                file_path=os.path.join(self.silver_dir,symbol,f"{stm}.csv")

                if os.path.exists(file_path):

                    df=pd.read_csv(file_path,index_col=0)

                    self._load_statement(session,df,company_id,stm)
                else:
                    logger.warning(f"silver file missing {symbol}:{stm} ")

            session.commit()
            logger.info(f"Successfully loaded all data for {symbol} into DB")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Database load error {symbol}:{e}")
            return False
        finally:
            session.close()

    def load_batch(self,company_list:List[str]):
        failed=[]
        for symbol in company_list:
            if not self._load_company_data(symbol):
                failed.append(symbol)
        return failed


if __name__ == "__main__":
    COMPANIES = ['TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'RELIANCE.NS']

    loader = DatabaseLoader()
    failures = loader.load_batch(COMPANIES)

    if not failures:
        logger.info("🚀 All data successfully moved to Gold Layer (Postgres)!")
    else:
        logger.warning(f"Load failed for: {failures}")
