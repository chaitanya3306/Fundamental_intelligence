import logging
from typing import List, Dict, Any


from ..financial_analysis.metrics import FinancialMetrics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RedFlagEngine:
    def __init__(self):
        self.metrics=FinancialMetrics()

    def check_cash_profit_gap(self,symbol)->Dict[str,Any]:
        """
        RULE: Profit is positive but Cash Flow from Operations is negative.
        """
        # logic: if PAT > 0 and CFO < 0: return True, "Profit exists but cash is negative"
        #get the latest values:
        net_income_series=self.metrics.get_metric_series(symbol,"Net Income")
        cfo_series=self.metrics.get_metric_series(symbol,"Free Cash Flow")

        if net_income_series.empty or cfo_series.empty:
            return {"triggered":False,"message":"Insufficient Data"}
        current_net_income=net_income_series.iloc[-1]
        current_cfo=cfo_series.iloc[-1]

        if current_net_income>0 and current_cfo<0:
            return {
                "triggered":True,
                "severity":"High",
                "message": "Net Income is positive but Cash Flow is negative. Potential aggressive accounting."
            }

        return {"triggered":False,"message":"Cash flow aligns with profit"}


    def check_receivables_trap(self, symbol:str)->Dict[str,Any]:
        # logic: if receivables_growth > revenue_growth: return True, "Receivables growing faster than sales"
        """
        RULE: Receivables are growing faster than Revenue.
        """
        rev_series = self.metrics.get_metric_series(symbol, "Total Revenue")
        rec_series = self.metrics.get_metric_series(symbol, "Total Receivables") # You might need to check the exact name in your CSVs
        if rev_series.empty or rec_series.empty or len(rev_series) < 2:
            return {"triggered": False, "message": "Insufficient data"}

        rev_growth=self.metrics.calculate_yoy_growth(rev_series.iloc[-1],rev_series.ilco[-2])
        rec_growth=self.metrics.calculate_yoy_growth(rec_series.iloc[-1],rec_series.ilco[-2])

        if rec_growth>rev_growth:
            return {
                "triggerd":True,
                "severity":"Medium",
                "message": f"Receivables growth "
                           f"({rec_growth:.2f}%) exceeds Revenue growth ({rev_growth:.2f}%)."
            }
        return {"triggerd":False,"message":"recivables growth is healthy"}


    def risk_audit(self, symbol):
        # Loop through all check functions and return a list of triggered flags
        logger.info(f"running audit for {symbol}")

        audit_result={
            "cash_profit gap":self.check_cash_profit_gap(symbol),
            "receivables_trap":self.check_receivables_trap(symbol)
        }

        return audit_result

if __name__=="__main__":
    risk_engine=RedFlagEngine()
    symbol="TCS.NS"
    report=risk_engine.risk_audit(symbol)

    print(f"Risk Audit for {symbol}:")
    for rule, result in report.items():
        status = "🚩 TRIGGERED" if result["triggered"] else "✅ CLEAN"
        print(f"{status} | {rule}: {result['message']}")






