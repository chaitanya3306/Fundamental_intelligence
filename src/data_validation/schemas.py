from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime,date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# data_contract
# ----------------------------------------------------------------------


class StatementType(str, Enum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASHFLOW = "cashflow"


class DataStatus(str, Enum):
    REPORTED = "reported"
    MISSING = "missing"
    INVALID = "invalid"
    NOT_APPLICABLE = "not_applicable"


class FinancialObservationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: int
    statement_type: StatementType
    reporting_date: date
    metric_name: str = Field(min_length=1)
    value: Optional[float] = None

    status: DataStatus
    currency: Optional[str] = None
    unit: Optional[str] = None
    source: str = "yfinance"
    ingested_at: datetime
    ingestion_run_id: Optional[str] = None