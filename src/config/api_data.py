# API data access layer – centralised fetching and caching

import logging
import os
from dotenv import load_dotenv

import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta, timezone

from ..database.session import db_manager
from ..database.models import Company

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Symbol mapping for external providers that use alternate ticker formats
SYMBOL_MAP = {
    "TATAMOTORS": "TMPV"
}

def _price_invalid(price: float) -> bool:
    """Return ``True`` if *price* is not a usable market price.

    A usable price must be a real number, not ``NaN``, not ``None`` and must be
    strictly greater than zero. ``pandas.isna`` is used for NaN detection.
    """
    if price is None:
        return True
    if pd.isna(price):
        return True
    try:
        return float(price) <= 0
    except (ValueError, TypeError):
        return True

def _fetch_from_finnhub(symbol: str) -> float:
    """Fetch the latest price from Finnhub.

    The function strips any trailing extension (e.g. ``.NS``) and applies the
    ``SYMBOL_MAP`` where required.  Returns ``float('nan')`` on any error.
    """
    try:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            return float('nan')
        clean_symbol = symbol.split('.')[0]
        api_symbol = SYMBOL_MAP.get(clean_symbol, clean_symbol)
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

    For Indian tickers we append ``.NS`` if missing.  The function prefers the
    ``fast_info['last_price']`` field, falling back to ``info['currentPrice']``
    or ``info['regularMarketPrice']``.
    """
    try:
        yf_symbol = symbol if '.' in symbol else f"{symbol}.NS"
        ticker = yf.Ticker(yf_symbol)
        price = ticker.fast_info.get('last_price')
        if price is None or pd.isna(price):
            price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
        if price is not None and not pd.isna(price):
            return float(price)
    except Exception as e:
        logger.error(f"YFinance Fallback Error for {symbol}: {e}")
    return float('nan')

def _fetch_from_infoway(symbol: str) -> float:
    """Fetch price via Infoway.

    The symbol is transformed to ``<ticker>.IN`` (or the mapped value for
    special cases) before calling the API.
    """
    try:
        infoway_symbol = symbol.split('.')[0] + '.IN'
        if infoway_symbol == "TATAMOTORS.IN":
            infoway_symbol = "TMPV.IN"
        api_key = os.getenv("INFOWAY_API_KEY")
        if not api_key:
            return float('nan')
        url = f"https://data.infoway.io/stock/batch_trade/{infoway_symbol}"
        headers = {"Accept": "application/json", "apiKey": api_key}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get('data'):
            price = data['data'][0].get('p')
            if price is not None:
                return float(price)
    except Exception as e:
        logger.error(f"INFOWAY Fallback Error for {symbol}: {e}")
    return float('nan')

def get_current_price(symbol: str) -> float:
    """Return the latest market price for *symbol*.

    The process follows a cache‑first strategy (valid for ``CACHE_AGE_DAYS`` days)
    and then falls back to the three external providers in order:
    Finnhub → YFinance → Infoway.  Only a price that passes ``_price_invalid``
    validation is cached.
    """
    # 1️⃣ Check DB cache
    session = db_manager.get_session()
    try:
        company = session.query(Company).filter(Company.ticker == symbol).first()
        if company and company.current_price is not None and company.last_updated:
            now = datetime.now(timezone.utc)
            last_updated = company.last_updated
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            cache_age = now - last_updated
            if cache_age < timedelta(days=1) and company.current_price > 0:
                logger.info(f"Cache Hit: Serving cached price for {symbol} (Age: {cache_age})")
                return company.current_price
    except Exception as e:
        logger.error(f"Cache read error for {symbol}: {e}")
    finally:
        session.close()

    # 2️⃣ Fetch fresh price
    price = _fetch_from_finnhub(symbol)
    if _price_invalid(price):
        logger.info(f"Finnhub returned invalid price for {symbol}; trying YFinance...")
        price = _fetch_from_yfinance(symbol)
    if _price_invalid(price):
        logger.info(f"YFinance returned invalid price for {symbol}; trying Infoway...")
        price = _fetch_from_infoway(symbol)

    # 3️⃣ Cache if valid
    if not _price_invalid(price):
        session = db_manager.get_session()
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

def get_shares_outstanding(symbol: str) -> float:
    """Return the number of shares outstanding for *symbol*.

    The function first attempts to read the value from the ``Company`` row.  If the
    value is missing it falls back to Yahoo Finance, caches the result and returns
    it.  ``float('nan')`` is returned on any failure.
    """
    # 1️⃣ Check DB cache
    session = db_manager.get_session()
    try:
        company = session.query(Company).filter(Company.ticker == symbol).first()
        if company and company.shares_outstanding:
            return company.shares_outstanding
    finally:
        session.close()

    # 2️⃣ Fetch via YFinance (the most reliable source for share counts)
    try:
        yf_symbol = symbol if '.' in symbol else f"{symbol}.NS"
        ticker = yf.Ticker(yf_symbol)
        shares = ticker.fast_info.get('shares_outstanding')
        if shares is None or pd.isna(shares):
            shares = ticker.info.get('sharesOutstanding')
        if shares:
            session = db_manager.get_session()
            try:
                company = session.query(Company).filter(Company.ticker == symbol).first()
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
    except Exception as e:
        logger.error(f"YFinance Shares Error for {symbol}: {e}")
    return float('nan')
