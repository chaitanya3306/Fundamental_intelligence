#in this file we check the current status of the company

import yfinance as yf
import pandas as pd


from ..database.session import db_manager
from ..database.models import Company,FinancialStatement
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValuationEngine:
    def __init__(self):
        self.db=db_manager

    def get_current_price(self,symbol): 
        logger.info(f"fetching price for {symbol}")
        try:
            ticker=yf.Ticker(symbol)
            price=ticker.fast_info['last_price']
            return price
        except Exception as e:
            logger.error(f"Error Fetching price for {symbol}:{e}")
            return float('nan')

    def get_shares_outstanding(self, symbol):
        logger.info(f"Fetching shares outstanding for {symbol}")
        try:
            ticker = yf.Ticker(symbol)

            # Strategy 1: Try fast_info (Fastest)
            info = ticker.fast_info
            if 'sharesOutstanding' in info:
                return info['sharesOutstanding']

            # Strategy 2: Try the main .info dictionary (More comprehensive)
            # This is slower but more reliable
            full_info = ticker.info
            if 'sharesOutstanding' in full_info:
                return full_info['sharesOutstanding']

            # Strategy 3: Try looking at the Balance Sheet (The most accurate)
            # We can find it in the balance sheet as 'Common Stock' or 'Total Equity' / 'Book Value'
            # But for now, we'll just log a warning.

            logger.warning(f"Could not find sharesOutstanding for {symbol} in fast_info or info")
            return float('nan')

        except Exception as e:
            logger.error(f"Critical error fetching shares for {symbol}: {e}")
            return float('nan')


    def calculate_relative_valuation(self,symbol):
        price=self.get_current_price(symbol)
        if pd.isna(price):return {"error":"price unavailable" }

        sharesOutstanding=self.get_shares_outstanding(symbol)
        if pd.isna(sharesOutstanding):return {"error":"sharesOutstanding unavailable" }

        session=self.db.get_session()


        try:
            # get netincome
            last_net_income=session.query(FinancialStatement).join(Company)\
                .filter(Company.ticker==symbol)\
                .filter(FinancialStatement.metric_name=='Net Income')\
                .order_by(FinancialStatement.date.desc()).first()
            #get equity
            last_equity=session.query(FinancialStatement).join(Company)\
                .filter(Company.ticker==symbol)\
                .filter(FinancialStatement.metric_name=='Total Equity') \
                .order_by(FinancialStatement.date.desc()).first()

            results={}

            if last_net_income:
                results['P/E_Ratio']=price/(last_net_income.value/sharesOutstanding)
            if last_equity:
                results['P/B_Ratio']=price/(last_equity.value/sharesOutstanding)

            return results
        finally: session.close()


    def calculate_dcf(self, symbol: str, growth_rate: float = 0.10, discount_rate: float = 0.12, terminal_growth: float = 0.03):
        """
        Calculates Intrinsic Value using a 5-year DCF model.
        growth_rate: Expected growth for the next 5 years (e.g., 0.10 for 10%)
        discount_rate: WACC / Required return (e.g., 0.12 for 12%)
        terminal_growth: Growth rate forever after year 5 (e.g., 0.03 for 3%)
        """

        # now we have to calculate the free_cash_flow entry latest and the shares_outstanding
        session=self.db.get_session()
        try:
            fcf_entry=session.query(FinancialStatement)\
                .join(Company).filter(Company.ticker==symbol)\
                .filter(FinancialStatement.metric_name=='Free Cash Flow' , FinancialStatement.statement_type=='cashflow')\
                .order_by(FinancialStatement.date.desc()).first()

            if not fcf_entry:
                return {"error": "FCF data missing for DCF"}

            #now get the shares
            shares=self.get_shares_outstanding(symbol)
            current_fcf=fcf_entry.value

            #now calculate projected_fcf for the 5 years with discount rate :
            projected_fcf=[]
            for year in range(1,6):
                fcf_year=current_fcf*((1+growth_rate)**year)
                #discount it back to present value FCF/(1+r)**t
                pv_fcf=fcf_year/((1+discount_rate)**year)
                projected_fcf.append(pv_fcf)

            #now calculating terminal value which tell what is the value after the 5 years fcf
            fcf_year_5=current_fcf*((1+growth_rate)**5)
            terminal_value=(fcf_year_5*(1+terminal_growth)/(discount_rate-terminal_growth))

            #discount the terminal value back today
            pv_terminal_value=terminal_value/(1+discount_rate)**5

            #total enterprise value
            enterprise_value=sum(projected_fcf)+pv_terminal_value

            intrinsic_value_per_share=enterprise_value/shares

            return {
                "intrinsic_value":intrinsic_value_per_share,
                "enterprise_value":enterprise_value,
                "assumptions":{
                    "growth_rate":growth_rate,
                    "discount_rate":discount_rate,
                    "terminal_growth":terminal_growth
                }
            }
        except Exception as e:
            logger.error(f"DCF Error for {symbol}: {e}")
            return {"error": str(e)}
        finally:
            session.close()

if __name__ == "__main__":
    engine = ValuationEngine()
    # Try a Bull Case: High growth (15%), Low discount (10%)
    print(engine.calculate_dcf("TCS.NS", growth_rate=0.15, discount_rate=0.10))




