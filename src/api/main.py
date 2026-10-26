from fastapi import FastAPI
import math

# Local service layer imports
from src.financial_analysis.metrics import FinancialMetrics
from src.risk_engine.red_flags import RedFlagEngine
from src.valuation.valuation import ValuationEngine

# Import the *new* response schemas that match the actual payloads
from src.api.schemas import (
    GrowthReportResponse,
    RiskAuditResponse,
    RelativeValuationResponse,
    DCFValuationResponse,
)

app = FastAPI()

# Service‑layer singletons (in‑memory, safe for this simple demo)
metrics_engine = FinancialMetrics()
risk_engine = RedFlagEngine()
valuation = ValuationEngine()


@app.get("/", response_model=dict)
async def root():
    return {"message": "Fundamental Analysis API is Online"}


# ---------------------------------------------------------------------
# 1️⃣  Growth / Metrics endpoint
# ---------------------------------------------------------------------
@app.get("/metrics/{symbol}", response_model=GrowthReportResponse)
async def get_financial_metrics(symbol: str):
    """Return growth metrics for *symbol*.

    The service layer returns a mapping ``metric → details``.  We wrap it
    with the ticker field required by the response model.
    """
    raw_metrics = metrics_engine.get_growth_report(symbol)
    payload = {"ticker": symbol, "metrics": raw_metrics}
    return clean_nan(payload)


# ---------------------------------------------------------------------
# 2️⃣  Risk‑audit endpoint
# ---------------------------------------------------------------------
@app.get("/risks/{symbol}", response_model=RiskAuditResponse)
async def get_risk_audit(symbol: str):
    """Run the red‑flag engine and expose a structured audit response.

    ``RedFlagEngine.risk_audit`` returns a dict of rule identifiers →
    {triggered, severity, message}.  We enrich that with summary lists
    ``red_flags`` (high severity) and ``warnings`` (medium severity) so the
    client can display concise highlights.
    """
    raw_rules = risk_engine.risk_audit(symbol)
    # Compute summary lists based on severity values
    red_flags = [name for name, r in raw_rules.items() if r.get("triggered") and r.get("severity", "").lower() == "high"]
    warnings = [name for name, r in raw_rules.items() if r.get("triggered") and r.get("severity", "").lower() == "medium"]
    payload = {
        "ticker": symbol,
        "overall_risk_score": None,
        "red_flags": red_flags,
        "warnings": warnings,
        "recommendation": None,
        "rules": raw_rules,
    }
    return clean_nan(payload)


# ---------------------------------------------------------------------
# 3️⃣  Relative‑valuation endpoint
# ---------------------------------------------------------------------
@app.get("/valuation/{symbol}", response_model=RelativeValuationResponse)
async def get_relative_valuation(symbol: str):
    """Return a handful of valuation multiples.

    The engine uses capital‑letter keys (e.g. ``"P/E_Ratio"``).  We
    translate them to the snake_case fields defined in the schema.
    """
    raw = valuation.calculate_relative_valuation(symbol)
    payload = {
        "ticker": symbol,
        "current_price": raw.get("current_price"),
        "pe_ratio": raw.get("P/E_Ratio"),
        "pb_ratio": raw.get("P/B_Ratio"),
        "ps_ratio": raw.get("P/S_Ratio"),
        "valuation_status": None,
    }
    return clean_nan(payload)


# ---------------------------------------------------------------------
# 4️⃣  Discounted‑cash‑flow (intrinsic) endpoint
# ---------------------------------------------------------------------
@app.get("/intrinsic/{symbol}", response_model=DCFValuationResponse)
async def get_intrinsic_value(
    symbol: str,
    growth: float = 0.10,
    discount: float = 0.12,
    terminal_growth: float = 0.03,
):
    """Run a DCF valuation with explicit assumptions.

    The engine returns ``intrinsic_value``, ``enterprise_value`` and the
    ``assumptions`` dict.  We also pull the latest market price from the
    relative‑valuation engine so the response can include ``current_price``
    and a derived ``upside_percent``.
    """
    dcf_raw = valuation.calculate_dcf(symbol, growth, discount, terminal_growth)
    # Obtain the latest price for the same symbol – reuse relative valuation.
    price_info = valuation.calculate_relative_valuation(symbol)
    current_price = price_info.get("current_price")

    payload = {
        "ticker": symbol,
        "intrinsic_value": dcf_raw.get("intrinsic_value"),
        "enterprise_value": dcf_raw.get("enterprise_value"),
        "current_price": current_price,
        "upside_percent": None,
        "assumptions": dcf_raw.get("assumptions", {
            "growth_rate": growth,
            "discount_rate": discount,
            "terminal_growth": terminal_growth,
        }),
        "warning": dcf_raw.get("warning") or dcf_raw.get("error"),
    }

    # Compute upside if we have both intrinsic value and a valid price.
    if (
        isinstance(payload["intrinsic_value"], (int, float))
        and isinstance(payload["current_price"], (int, float))
        and payload["current_price"] != 0
    ):
        try:
            payload["upside_percent"] = ((payload["intrinsic_value"] - payload["current_price"]) / payload["current_price"]) * 100
        except Exception:
            payload["upside_percent"] = None

    return clean_nan(payload)


def clean_nan(obj):
    """Recursively replace NaN values with ``None`` for JSON compliance."""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(x) for x in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    return obj
