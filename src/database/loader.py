"""Load normalized Silver-layer statements into the relational Gold layer."""
import logging
import math
import os
from pathlib import Path
from types import SimpleNamespace
from typing import List

import pandas as pd

from .models import Company, FinancialStatement
from .session import db_manager

logger = logging.getLogger(__name__)
STATEMENTS = ("income_statement", "balance_sheet", "cashflow")


class DatabaseLoader:
    # Kept as a compatibility surface for existing tests and callers.
    model = SimpleNamespace(Company=Company, FinancialStatement=FinancialStatement)

    def __init__(self, silver_dir: str = "data/silver"):
        self.silver_dir = os.getenv("FINANCIAL_SILVER_DIR", silver_dir)

    def _get_or_create_company(self, session, symbol: str) -> int:
        company = session.query(Company).filter(Company.ticker == symbol).first()
        if company is None:
            company = Company(ticker=symbol)
            session.add(company)
            session.flush()
        return company.company_id

    def _upsert_statement(
        self, session, company_id: int, statement_type: str,
        report_date, metric_name: str, value: float
    ) -> None:
        existing = (
            session.query(FinancialStatement)
            .filter(
                FinancialStatement.company_id == company_id,
                FinancialStatement.date == report_date,
                FinancialStatement.statement_type == statement_type,
                FinancialStatement.metric_name == metric_name,
            )
            .first()
        )
        if existing is not None:
            existing.value = value
        else:
            session.add(
                FinancialStatement(
                    company_id=company_id,
                    date=report_date,
                    statement_type=statement_type,
                    metric_name=metric_name,
                    value=value,
                )
            )

    def _load_statement(self, session, df: pd.DataFrame, company_id: int, statement_type: str) -> int:
        """Load Silver format: date index, one column per financial metric."""
        loaded = 0
        for date_value, row in df.iterrows():
            report_date = pd.to_datetime(date_value, errors="raise").date()
            for metric_name, raw_value in row.items():
                if pd.isna(raw_value):
                    continue
                value = float(raw_value)
                if not math.isfinite(value):
                    raise ValueError(
                        f"Non-finite value for {statement_type}.{metric_name} on {report_date}"
                    )
                self._upsert_statement(
                    session, company_id, statement_type, report_date, str(metric_name), value
                )
                loaded += 1
        return loaded

    def _load_company_data(self, symbol: str) -> bool:
        folder = Path(self.silver_dir) / symbol
        missing = [
            name for name in STATEMENTS
            if not (folder / f"{name}.csv").is_file()
        ]
        if missing:
            logger.error(
                "Refusing to load incomplete Silver data for %s in %s; missing statements: %s",
                symbol,
                folder,
                missing,
            )
            return False

        session = db_manager.get_session()
        try:
            company_id = self._get_or_create_company(session, symbol)
            loaded = 0
            for statement_type in STATEMENTS:
                path = folder / f"{statement_type}.csv"
                df = pd.read_csv(path, index_col=0)
                if df.empty:
                    logger.warning("Skipping empty Silver statement %s", path)
                    continue
                loaded += self._load_statement(session, df, company_id, statement_type)

            if loaded == 0:
                raise ValueError(f"No non-missing financial observations available for {symbol}")

            session.commit()
            logger.info("Loaded %d observations for %s", loaded, symbol)
            return True
        except Exception:
            session.rollback()
            logger.exception("Database load failed for %s", symbol)
            return False
        finally:
            session.close()

    def load_batch(self, company_list: List[str]) -> List[str]:
        return [symbol for symbol in company_list if not self._load_company_data(symbol)]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    failures = DatabaseLoader().load_batch(["AAPL", "MSFT", "GOOGL", "AMZN", "META"])
    if failures:
        logger.error("Database load failed for: %s", failures)
    else:
        logger.info("All requested data loaded.")
