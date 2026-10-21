import logging
from src.database.session import db_manager
from src.database.models import Company
from src.config.api_data import CurrentData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reset_shares(tickers):
    # Clear cached shares for given tickers
    session = db_manager.get_session()
    try:
        for sym in tickers:
            company = session.query(Company).filter(Company.ticker == sym).first()
            if company:
                company.shares_outstanding = None
                logger.info(f"Cleared shares_outstanding for {sym}")
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing shares: {e}")
    finally:
        session.close()

    # Re-fetch shares using placeholder values (avoiding API rate limits)
    placeholder_shares = {
        "AAPL": 15800000000.0,
        "MSFT": 7500000000.0,
        "GOOGL": 3000000000.0,
        "AMZN": 5000000000.0,
        "META": 2600000000.0,
        "TSLA": 3200000000.0,
        "NVDA": 2500000000.0,
    }
    session = db_manager.get_session()
    try:
        for sym in tickers:
            shares = placeholder_shares.get(sym)
            if shares is not None:
                company = session.query(Company).filter(Company.ticker == sym).first()
                if company:
                    company.shares_outstanding = shares
                    logger.info(f"Set placeholder shares for {sym}: {shares}")
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error setting placeholder shares: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    # Define the ticker list (must match those in the pipeline)
    ticker_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"]
    reset_shares(ticker_list)
