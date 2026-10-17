# in this file we check the current status of the company

import logging
import os
from dotenv import load_dotenv

import pandas as pd

from ..database.session import db_manager
from ..database.models import Company, FinancialStatement
from src.config.api_data import CurrentData

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ValuationEngine:
    def __init__(self):
        self.db = db_manager
        self._data = CurrentData()

    def calculate_relative_valuation(self, symbol: str):
        """Calculate basic relative valuation metrics for the given *symbol*.

        Returns a dictionary containing ``current_price`` (or ``None`` if unavailable) and, when possible, ``P/E_Ratio`` and ``P/B_Ratio``. If the share count or price is missing, those ratios are omitted but ``current_price`` is still returned.
        """

        price = self._data.get_current_price(symbol)
        shares_outstanding = self._data.get_shares_outstanding(symbol)
        shares_valid = not pd.isna(shares_outstanding)
        price_valid = not pd.isna(price)

        # Base result always includes the current price (or None)
        results = {"current_price": None if pd.isna(price) else price}

        # Include shares if available (useful for callers that may need it)
        if shares_valid:
            results["shares_outstanding"] = shares_outstanding

        session = self.db.get_session()
        try:
            last_net_income = (
                session.query(FinancialStatement)
                .join(Company)
                .filter(Company.ticker == symbol)
                .filter(FinancialStatement.metric_name == 'Net Income')
                .order_by(FinancialStatement.date.desc())
                .first()
            )

            last_equity = (
                session.query(FinancialStatement)
                .join(Company)
                .filter(Company.ticker == symbol)
                .filter(FinancialStatement.metric_name == 'Total Equity')
                .order_by(FinancialStatement.date.desc())
                .first()
            )

            if price_valid and shares_valid and last_net_income:
                results['P/E_Ratio'] = price / (last_net_income.value / shares_outstanding)
            if price_valid and shares_valid and last_equity:
                results['P/B_Ratio'] = price / (last_equity.value / shares_outstanding)

            return results
        finally:
            session.close()

    def calculate_dcf(self, symbol: str, growth_rate: float = 0.10, discount_rate: float = 0.12, terminal_growth: float = 0.03):
        """Discounted cash‑flow valuation.

        *growth_rate*, *discount_rate* and *terminal_growth* are validated to be
        positive numbers.  A ``ZeroDivisionError`` is avoided by ensuring that
        ``discount_rate`` is strictly greater than ``terminal_growth``.
        """
        # Basic parameter validation – defensive coding for production robustness.
        if growth_rate < 0:
            raise ValueError("growth_rate must be non‑negative")
        if discount_rate <= 0:
            raise ValueError("discount_rate must be positive")
        if terminal_growth < 0:
            raise ValueError("terminal_growth must be non‑negative")
        if discount_rate <= terminal_growth:
            raise ValueError("discount_rate must be greater than terminal_growth to avoid division by zero")

        shares = self._data.get_shares_outstanding(symbol)
        if pd.isna(shares):
            logger.warning(f"Shares Outstanding unavailable for {symbol}; DCF cannot be computed")
            # Return placeholder with None values instead of an error
            return {
                "intrinsic_value": None,
                "enterprise_value": None,  # Fixed typo (was "enterprise,value")
                "assumptions": {
                    "growth_rate": growth_rate,
                    "discount_rate": discount_rate,
                    "terminal_growth": terminal_growth,
                },
                "warning": "sharesOutstanding unavailable"
            }

        session = self.db.get_session()
        try:
            fcf_entry = (
                session.query(FinancialStatement)
                .join(Company)
                .filter(Company.ticker == symbol)
                .filter(FinancialStatement.metric_name == 'Free Cash Flow', FinancialStatement.statement_type == 'cashflow')
                .order_by(FinancialStatement.date.desc())
                .first()
            )

            if not fcf_entry:
                return {"error": "FCF data missing for DCF"}

            current_fcf = fcf_entry.value
            if current_fcf <= 0:
                logger.warning(f"FCF for {symbol} is non‑positive ({current_fcf}); DCF will return NaN")
                return {"error": "FCF non‑positive, cannot compute DCF"}

            projected_fcf = []
            for year in range(1, 6):
                fcf_year = current_fcf * ((1 + growth_rate) ** year)
                pv_fcf = fcf_year / ((1 + discount_rate) ** year)
                projected_fcf.append(pv_fcf)

            fcf_year_5 = current_fcf * ((1 + growth_rate) ** 5)
            terminal_value = (fcf_year_5 * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            pv_terminal_value = terminal_value / ((1 + discount_rate) ** 5)
            enterprise_value = sum(projected_fcf) + pv_terminal_value
            intrinsic_value_per_share = enterprise_value / shares

            return {
                "intrinsic_value": intrinsic_value_per_share,
                "enterprise_value": enterprise_value,
                "assumptions": {
                    "growth_rate": growth_rate,
                    "discount_rate": discount_rate,
                    "terminal_growth": terminal_growth,
                },
            }
        except Exception as e:
            logger.error(f"DCF Error for {symbol}: {e}")
            return {"error": str(e)}
        finally:
            session.close()


if __name__ == "__main__":
    engine = ValuationEngine()
    print(engine.calculate_dcf("TCS.NS", growth_rate=0.15, discount_rate=0.10))
