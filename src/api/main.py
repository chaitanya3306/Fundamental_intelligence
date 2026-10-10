from fastapi import FastAPI
import math
from src.financial_analysis.metrics import FinancialMetrics
from src.risk_engine.red_flags import RedFlagEngine
from src.valuation.valuation import ValuationEngine


app=FastAPI()

metrics_engine=FinancialMetrics()
risk_engine=RedFlagEngine()
valuation=ValuationEngine()


@app.get("/")
async  def root():
    return {"message": "Fundamental Analysis API is Online"}

@app.get("/metrics/{symbol}")
async def get_financial_metrics(symbol:str):
    return  metrics_engine.get_growth_report(symbol)

@app.get("/risks/{symbol}")
async def get_risk_audit(symbol:str):
    return risk_engine.risk_audit(symbol)

@app.get("/valuation/{symbol}")
async def get_relative_valuation(symbol:str):
    res= valuation.calculate_relative_valuation(symbol)
    return clean_nan(res)

def clean_nan(obj):
    """Recursively replace NaN values with None for JSON compliance."""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(x) for x in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    return obj

@app.get("/intrinsic/{symbol}")
async def get_intrinsic_value(symbol: str, growth: float = 0.10, discount: float = 0.12,terminal_growth:float=0.03):
    res=valuation.calculate_dcf(symbol,growth,discount,terminal_growth)
    return clean_nan(res)




