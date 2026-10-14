# in this file we check the current status of the company

import yfinance as yf
import pandas as pd
import requests
import logging
import os
from dotenv import load_dotenv

from datetime import datetime, timedelta, timezone

from ..database.session import db_manager
from ..database.models import Company, FinancialStatement

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValuationEngine:
    def __init__(self):
        self.db = db_manager
        self.CACHE_AGE_DAYS = 1
        # Symbol mapping for APIs that use different identifiers
        self.symbol_map = {
            "TATAMOTORS": "TMPV"
        }

    def get_current_price(self, symbol: str) -> float:
        logger.info(f"requesting price for {symbol}")

        # 1. Check the database cache
        session = self.db.get_session()
        try:
            company = session.query(Company).filter(Company.ticker == symbol).first()

            if company and company.current_price and company.last_updated:
                now = datetime.now(timezone.utc)
                last_updated = company.last_updated
                if last_updated.tzinfo is None:
                    last_updated = last_updated.replace(tzinfo=timezone.utc)

                cache_age = now - last_updated
                if cache_age < timedelta(days=self.CACHE_AGE_DAYS):
                    logger.info(f"Cache Hit: Serving cached price for {symbol} (Age: {cache_age})")
                    return company.current_price
        finally:
            session.close()

        # 2. Fetch fresh price using Waterfall Strategy
        logger.info(f"Cache expired or missing. Fetching fresh price for {symbol}...")

        # Try Finnhub first (Fastest)
        price = self._fetch_from_finnhub(symbol)

        # Fallback to YFinance if Finnhub fails or returns 0 (Common for Indian stocks)
        if pd.isna(price):
            logger.info(f"Finnhub failed for {symbol}. Trying YFinance fallback...")
            price = self._fetch_from_yfinance(symbol)
            if pd.isna(price):
                price=self._fetch_from_infoway(symbol)


        # 3. Update cache if we found a valid price
        if not pd.isna(price):
            session = self.db.get_session()
            try:
                company = session.query(Company).filter(Company.ticker == symbol).first()
                if company:
                    company.current_price = price
                    company.last_updated = datetime.now(timezone.utc)
                    session.commit()
            finally:
                session.close()

        return price

    def _fetch_from_finnhub(self, symbol: str) -> float:
        """Helper to fetch price from Finnhub API."""
        try:
            api_key = os.getenv("FINNHUB_API_KEY")
            if not api_key:
                return float('nan')

            # Strip any extension (e.g., ".NS") and apply the mapping dictionary
            clean_symbol = symbol.split('.')[0]
            api_symbol = self.symbol_map.get(clean_symbol, clean_symbol)

            url = f"https://finnhub.io/api/v1/quote?symbol={api_symbol}&token={api_key}"
            response = requests.get(url, timeout=5)
            data = response.json()

            if 'c' in data and data['c'] != 0:
                return float(data['c'])
        except Exception as e:
            logger.error(f"Finnhub API Error for {symbol}: {e}")
        return float('nan')

    def _fetch_from_yfinance(self, symbol: str) -> float:
        try:
            yf_symbol = symbol if "." in symbol else f"{symbol}.NS"

            ticker = yf.Ticker(yf_symbol)

            price = ticker.fast_info.get("last_price")

            if price is None or pd.isna(price):
                price = (
                        ticker.info.get("currentPrice")
                        or ticker.info.get("regularMarketPrice")
                )

            if price is not None and not pd.isna(price):
                return float(price)

        except Exception as e:
            logger.error(f"YFinance Fallback Error for {symbol}: {e}")

        return float("nan")

    def _fetch_from_infoway(self, symbol: str) -> float:
        try:
            infoway_symbol = symbol.split(".")[0] + ".IN"

            if infoway_symbol == "TATAMOTORS.IN":
                infoway_symbol = "TMPV.IN"

            api_key = os.getenv("INFOWAY_API_KEY")

            api_url = (
                f"https://data.infoway.io/stock/batch_trade/{infoway_symbol}"
            )

            headers = {
                "Accept": "application/json",
                "apiKey": api_key,
            }

            response = requests.get(
                api_url,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            if data.get("data"):
                price = data["data"][0].get("p")

                if price is not None:
                    return float(price)

        except Exception as e:
            logger.error(f"INFOWAY Fallback Error for {symbol}: {e}")

        return float("nan")


    def get_shares_outstanding(self, symbol: str) -> float:
        logger.info(f"Checking shares outstanding for {symbol}")

        # 1. Try Database (Cache)
        session = self.db.get_session()
        try:
            company = session.query(Company).filter(Company.ticker == symbol).first()
            if company and company.shares_outstanding:
                return company.shares_outstanding
        finally:
            session.close()

        # 2. API Fallback
        try:
            yf_symbol = symbol if '.' in symbol else f"{symbol}.NS"
            ticker = yf.Ticker(yf_symbol)

            # Strategy: Try fast_info first (most reliable for shares), then fallback to info
            shares = ticker.fast_info.get('shares_outstanding')
            if shares is None or pd.isna(shares):
                shares = ticker.info.get('sharesOutstanding')

            if shares:
                session = self.db.get_session()
                try:
                    company = session.query(Company).filter(Company.ticker == symbol).first()
                    if company:
                        company.shares_outstanding = shares
                        session.commit()
                finally:
                    session.close()
                return shares
        except Exception as e:
            logger.error(f"YFinance Shares Error for {symbol}: {e}")

        return float('nan')

    def calculate_relative_valuation(self, symbol: str):
        price = self.get_current_price(symbol)
        shares_outstanding = self.get_shares_outstanding(symbol)
        if pd.isna(shares_outstanding):
            return {"error": "sharesOutstanding unavailable"}

        session = self.db.get_session()
        try:
            last_net_income = session.query(FinancialStatement).join(Company)\
                .filter(Company.ticker == symbol)\
                .filter(FinancialStatement.metric_name == 'Net Income')\
                .order_by(FinancialStatement.date.desc()).first()

            last_equity = session.query(FinancialStatement).join(Company)\
                .filter(Company.ticker == symbol)\
                .filter(FinancialStatement.metric_name == 'Total Equity') \
                .order_by(FinancialStatement.date.desc()).first()

            results = {}
            results['current_price'] = None if pd.isna(price) else price

            if not pd.isna(price) and last_net_income:
                results['P/E_Ratio'] = price / (last_net_income.value / shares_outstanding)
            if not pd.isna(price) and last_equity:
                results['P/B_Ratio'] = price / (last_equity.value / shares_outstanding)

            return results
        finally:
            session.close()

    def calculate_dcf(self, symbol: str, growth_rate: float = 0.10, discount_rate: float = 0.12, terminal_growth: float = 0.03):
        session = self.db.get_session()
        try:
            fcf_entry = session.query(FinancialStatement)\
                .join(Company).filter(Company.ticker == symbol)\
                .filter(FinancialStatement.metric_name == 'Free Cash Flow', FinancialStatement.statement_type == 'cashflow')\
                .order_by(FinancialStatement.date.desc()).first()

            if not fcf_entry:
                return {"error": "FCF data missing for DCF"}

            shares = self.get_shares_outstanding(symbol)
            if pd.isna(shares): return {"error": "sharesOutstanding unavailable"}

            current_fcf = fcf_entry.value
            projected_fcf = []
            for year in range(1, 6):
                fcf_year = current_fcf * ((1 + growth_rate)**year)
                pv_fcf = fcf_year / ((1 + discount_rate)**year)
                projected_fcf.append(pv_fcf)

            fcf_year_5 = current_fcf * ((1 + growth_rate)**5)
            terminal_value = (fcf_year_5 * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            pv_terminal_value = terminal_value / ((1 + discount_rate)**5)
            enterprise_value = sum(projected_fcf) + pv_terminal_value
            intrinsic_value_per_share = enterprise_value / shares

            return {
                "intrinsic_value": intrinsic_value_per_share,
                "enterprise,value": enterprise_value,
                "assumptions": {
                    "growth_rate": growth_rate,
                    "discount_rate": discount_rate,
                    "terminal_growth": terminal_growth
                }
            }
        except Exception as e:
            logger.error(f"DCF Error for {symbol}: {e}")
            return {"error": str(e)}
        finally:
            session.close()


if __name__ == "__main__":
    engine = ValuationEngine()
    print(engine.calculate_dcf("TCS.NS", growth_rate=0.15, discount_rate=0.10))
