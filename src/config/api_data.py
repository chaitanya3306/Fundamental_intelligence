import logging
import os
from dotenv import load_dotenv

import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta, timezone

from ..database.session import db_manager
from ..database.models import Company

# No market suffix helper – we treat symbols as plain US tickers.

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _price_invalid(price: float) -> bool:
    """Return ``True`` if *price* is not a usable market price.

    A usable price must be a real number, not ``NaN``, not ``None`` and must be
    strictly greater than zero.
    """
    if price is None:
        return True
    if pd.isna(price):
        return True
    try:
        return float(price) <= 0
    except (ValueError, TypeError):
        return True


def _shares_invalid(shares) -> bool:
    if shares is None:
        return True
    try:
        shares = float(shares)
        if pd.isna(shares):
            return True
        return shares <= 0
    except (ValueError, TypeError):
        return True


def _fetch_from_finnhub(symbol: str) -> float:
    """Fetch the latest price from Finnhub.

    Finnhub works for US symbols as well, but we keep the same logic – it strips any
    trailing extension and uses the raw ticker.
    """
    try:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            return float('nan')
        api_symbol = symbol.split('.')[0]
        url = f"https://finnhub.io/api/v1/quote?symbol={api_symbol}&token={api_key}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if 'c' in data and data['c'] != 0:
            return float(data['c'])
    except Exception as e:
        logger.error(f"Finnhub API Error for {symbol}: {e}")
    return float('nan')


def _fetch_from_yfinance(symbol: str) -> float:
    """Fetch price via Yahoo Finance.

    The ticker is used exactly as supplied (no market‑suffix manipulation). The
    function prefers ``fast_info['last_price']`` and falls back to ``info`` fields.
    """
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.fast_info.get('last_price')
        if price is None or pd.isna(price):
            price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
        if price is not None and not pd.isna(price):
            return float(price)
    except Exception as e:
        logger.error(f"YFinance error for {symbol}: {e}")
    return float('nan')




def _fetch_shares_from_yfinance(symbol: str) -> float:
    """Fetch shares outstanding via Yahoo Finance.

    Returns the number of shares outstanding if available, otherwise NaN.
    """
    try:
        ticker = yf.Ticker(symbol)
        shares = ticker.info.get('sharesOutstanding')
        if shares is not None and not pd.isna(shares):
            return float(shares)
    except Exception as e:
        logger.error(f"YFinance shares error for {symbol}: {e}")
    return float('nan')
def _fetch_from_infoway(symbol: str) -> float:
    """Infoway is India‑specific and is disabled in the US‑only version.

    We simply return ``nan`` and log that the provider is skipped.
    """
    logger.info(f"Infoway provider skipped for US ticker {symbol}")
    return float('nan')


class CurrentData:
    def __init__(self):
        self.db = db_manager
        self.CACHE_EXPIRY = 1

    def get_current_price(self, symbol: str) -> float:
        """Return the latest market price for *symbol*.

        The lookup follows a cache‑first strategy (valid for ``CACHE_EXPIRY`` days)
        and then falls back to Finnhub → YFinance.  Infoway is not used for US data.
        """
        # 1️⃣ Check DB cache
        session = self.db.get_session()
        try:
            company = session.query(Company).filter(Company.ticker == symbol).first()
            if company and company.current_price is not None and company.last_updated:
                now = datetime.now(timezone.utc)
                last_updated = company.last_updated
                if last_updated.tzinfo is None:
                    last_updated = last_updated.replace(tzinfo=timezone.utc)
                cache_age = now - last_updated
                if cache_age < timedelta(days=self.CACHE_EXPIRY) and company.current_price > 0:
                    logger.info(f"Cache Hit: Serving cached price for {symbol} (Age: {cache_age})")
                    return company.current_price
        except Exception as e:
            logger.error(f"Cache read error for {symbol}: {e}")
        finally:
            session.close()

        # 2️⃣ Fetch fresh price (Finnhub -> YFinance)
        price = _fetch_from_finnhub(symbol)
        if _price_invalid(price):
            logger.info(f"Finnhub returned invalid price for {symbol}; trying YFinance...")
            price = _fetch_from_yfinance(symbol)
        # Infoway is not attempted in the US‑only version.

        # 3️⃣ Cache if valid
        if not _price_invalid(price):
            session = self.db.get_session()
            try:
                company = session.query(Company).filter(Company.ticker == symbol).first()
                if not company:
                    company = Company(ticker=symbol)
                    session.add(company)
                    session.flush()
                company.current_price = price
                company.last_updated = datetime.now(timezone.utc)
                session.commit()
            except Exception as e:
                logger.error(f"Failed to cache price for {symbol}: {e}")
                session.rollback()
            finally:
                session.close()
        else:
            logger.warning(f"All price providers failed for {symbol}; returning NaN.")
        return price

    def get_shares_outstanding(self, symbol: str) -> float:
        session = self.db.get_session()
        try:
            company = (
                session.query(Company)
                .filter(Company.ticker == symbol)
                .first()
            )
            if (
                company
                and company.shares_outstanding
                and company.shares_outstanding > 0
            ):
                return company.shares_outstanding
        finally:
            session.close()

        # Use YFinance for shares
        shares = _fetch_shares_from_yfinance(symbol)
        if _shares_invalid(shares):
            logger.info(f"YFinance shares unavailable for {symbol}")
        if not _shares_invalid(shares):
            session = self.db.get_session()
            try:
                company = (
                    session.query(Company)
                    .filter(Company.ticker == symbol)
                    .first()
                )
                if not company:
                    company = Company(ticker=symbol)
                    session.add(company)
                    session.flush()
                company.shares_outstanding = shares
                session.commit()
            except Exception as e:
                logger.error(f"Failed to cache shares for {symbol}: {e}")
                session.rollback()
            finally:
                session.close()
            return shares
        logger.warning(f"All shares‑outstanding providers failed for {symbol}")
        return float('nan')


if __name__ == "__main__":
    print("******  Fetching the data *******")
    print(f"yfinance :{_fetch_from_yfinance('AAPL')}")
    print(f"finnhub :{_fetch_from_finnhub('AAPL')}")
    print("Infoway is disabled for US data.")
    current_data = CurrentData()
    print(current_data.get_current_price('AAPL'))
    print(current_data.get_shares_outstanding('AAPL'))
