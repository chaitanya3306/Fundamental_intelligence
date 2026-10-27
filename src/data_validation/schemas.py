
"""Canonical data contract for financial statement observations."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StatementType(str, Enum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASHFLOW = "cashflow"


class DataStatus(str, Enum):
    REPORTED = "reported"
    MISSING = "missing"
    INVALID = "invalid"
    NOT_APPLICABLE = "not_applicable"
    NOT_SUPPLIED = "not_supplied"


class FinancialObservationSchema(BaseModel):
    """One metric observation for one company and reporting period."""

    model_config = ConfigDict(extra="forbid")

    company_id: int = Field(gt=0)
    statement_type: StatementType
    reporting_date: date
    metric_name: str = Field(min_length=1)

    value: Optional[float] = None
    status: DataStatus

    currency: Optional[str] = None
    unit: Optional[str] = None

    source: str = Field(min_length=1)
    ingested_at: datetime
    ingestion_run_id: Optional[str] = None

    @field_validator("metric_name")
    @classmethod
    def normalize_metric_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("metric_name cannot be blank")

        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("source cannot be blank")

        return value

    @field_validator("currency", "unit")
    @classmethod
    def normalize_optional_metadata(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()

        return value or None
