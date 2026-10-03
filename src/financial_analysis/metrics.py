import pandas as pd
import logging
from typing import List, Dict, Any
from datetime import date


from ..database.session import db_manager
from ..database.models import FinancialStatement, Company

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialMetrics:
    def __init__(self):
        self.db=db_manager

    def calculate_yoy_growth(self,current_val:float,previous_val:float)->float:
        if previous_val==0.0 or previous_val<0.0:
            logger.warning(f"Undefined YoY Growth: Previous value is {previous_val}")
            return float('nan')

        yoy_growth=((current_val-previous_val)/previous_val)*100

        return yoy_growth

    def calculate_cagr(self,beginning_val:float,ending_val:float,periods:int)->float:

        if beginning_val <= 0 or ending_val <= 0 or periods <= 0:
            logger.warning(f"Undefined CAGR: Beg={beginning_val}, End={ending_val}, P={periods}")
            return float('nan')


        cagr = ((ending_val / beginning_val) ** (1 / periods)) - 1
        return cagr

    def get_metric_series(self,symbol:str,metric_name:str)->pd.Series:
        try:
            session=self.db.get_session()
            results=session.query(FinancialStatement).join(Company)\
            .filter(Company.ticker==symbol).filter(FinancialStatement.metric_name==metric_name)\
            .all()

            data={r.date:r.value for r in results}
            series=pd.Series(data)
            series.index=pd.to_datetime(series.index)
            return series

        except Exception as e:
            logger.error(f"Error Fetching Series For {symbol}:{metric_name} :{e}")
            return pd.Series(dtype=float)
        finally:
            session.close()

    def get_growth_report(self,symbol:str):
        report={}
        target_metrics = ["Total Revenue", "Net Income", "EBITDA"]
        for metric in target_metrics:
            series=self.get_metric_series(symbol,metric)

            if len(series)<2:
                report[metric]={"error":"not enough data points"}

            current_val=series.iloc[-1]
            previous_val=series.iloc[-2]
            beginning_val=series.iloc[0]
            periods=len(series)-1

            report[metric]={
                "current_value":current_val,
                "yoy_growth":self.calculate_yoy_growth(current_val,previous_val),
                "cagr":self.calculate_cagr(beginning_val,current_val,periods)
            }
        return report

if __name__=="__main__":
    metrics=FinancialMetrics()
    symbol="TCS.NS"
    report=metrics.get_growth_report(symbol)
    print(f"Growth Report For {symbol}: \n {report}")

