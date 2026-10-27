# src/api/schemas.py
"""
FastAPI response schemas for FinSight AI.

These models are deliberately *aligned* with the dictionaries produced by the
service layer (FinancialMetrics, RedFlagEngine, ValuationEngine) so FastAPI can
validate the output without raising a ``422`` error.  They also drive the
OpenAPI documentation shown at ``/docs``.
"""

from __future__ import annotations

from datetime import datetime,date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field



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







# ----------------------------------------------------------------------
# 1️⃣  Growth / Metrics endpoint
# ----------------------------------------------------------------------
class MetricDetail(BaseModel):
    """Details for a single financial metric.

    ``current_value`` – most recent observation (float or ``None``).
    ``yoy_growth`` – year‑over‑year growth in percent (may be ``None``).
    ``cagr`` – compound annual growth rate over the observed series.
    """

    current_value: Optional[float] = Field(
        default=None, description="Latest reported value for the metric."
    )
    yoy_growth: Optional[float] = Field(
        default=None, description="YoY growth percentage, ``None`` if undefined."
    )
    cagr: Optional[float] = Field(
        default=None, description="Compound annual growth rate over the period."
    )


class GrowthReportResponse(BaseModel):
    """Response model for ``GET /metrics/{symbol}``.

    The ``metrics`` dictionary is keyed by the metric name exactly as it
    appears in the source data (e.g. "Total Revenue").
    """

    ticker: str = Field(..., description="Company ticker symbol, e.g. AAPL.")
    metrics: Dict[str, MetricDetail] = Field(
        default_factory=dict,
        description="Mapping from metric name → its details.",
    )


# ----------------------------------------------------------------------
# 2️⃣  Risk‑audit endpoint
# ----------------------------------------------------------------------
class RuleResult(BaseModel):
    """Result for a single red‑flag rule."""

    triggered: bool = Field(..., description="True if the rule fired.")
    severity: str = Field(..., description="Risk severity – Low/Medium/High.")
    message: str = Field(..., description="Human‑readable explanation of the finding.")


class RiskAuditResponse(BaseModel):
    """Aggregated risk‑audit information for ``GET /risks/{symbol}``."""

    ticker: str = Field(..., description="Company ticker.")
    overall_risk_score: Optional[float] = Field(
        default=None, description="Composite numeric risk score (optional)."
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="List of rule identifiers that triggered with *High* severity.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of rule identifiers that triggered with *Medium* severity.",
    )
    recommendation: Optional[str] = Field(
        default=None, description="High‑level recommendation based on the audit (optional)."
    )
    rules: Dict[str, RuleResult] = Field(
        default_factory=dict,
        description="All individual rule results keyed by rule identifier.",
    )


# ----------------------------------------------------------------------
# 3️⃣  Relative‑valuation endpoint
# ----------------------------------------------------------------------
class RelativeValuationResponse(BaseModel):
    """Key valuation multiples for ``GET /valuation/{symbol}``."""

    ticker: str = Field(..., description="Company ticker.")
    current_price: Optional[float] = Field(
        default=None, description="Latest market price (or ``None`` if unavailable)."
    )
    pe_ratio: Optional[float] = Field(
        default=None, description="Price‑to‑Earnings ratio."
    )
    pb_ratio: Optional[float] = Field(
        default=None, description="Price‑to‑Book ratio."
    )
    ps_ratio: Optional[float] = Field(
        default=None, description="Price‑to‑Sales ratio."
    )
    valuation_status: Optional[str] = Field(
        default=None,
        description="Arbitrary status string, e.g. \"Undervalued\"/\"Overvalued\".",
    )


# ----------------------------------------------------------------------
# 4️⃣  Discounted cash‑flow (DCF) endpoint
# ----------------------------------------------------------------------
class DCFAssumptions(BaseModel):
    """The three numeric assumptions used for the DCF calculation."""

    growth_rate: float = Field(..., description="Projected cash‑flow growth (decimal).")
    discount_rate: float = Field(..., description="Discount rate applied to future cash flows (decimal).")
    terminal_growth: float = Field(..., description="Long‑run growth rate after the explicit forecast window (decimal).")


class DCFValuationResponse(BaseModel):
    """Result of a DCF valuation (``GET /intrinsic/{symbol}``)."""

    ticker: str = Field(..., description="Company ticker.")
    intrinsic_value: Optional[float] = Field(
        default=None,
        description="Per‑share intrinsic (DCF) value.",
    )
    enterprise_value: Optional[float] = Field(
        default=None,
        description="Total firm value before dividing by shares outstanding.",
    )
    current_price: Optional[float] = Field(
        default=None,
        description="Latest market price – useful for computing upside.",
    )
    upside_percent: Optional[float] = Field(
        default=None,
        description="((intrinsic – price) / price) * 100, if both are present.",
    )
    assumptions: DCFAssumptions = Field(..., description="The assumptions used for this calculation.")
    warning: Optional[str] = Field(
        default=None,
        description="If the DCF could not be computed (e.g., missing shares).",
    )
