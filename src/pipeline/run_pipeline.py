import logging

from src.data_ingestion.fetch_basics import YFinanceFetcher
from src.data_cleaning.cleaner import FinancialCleaner
from src.database.loader import DatabaseLoader
from src.database.session import db_manager


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Ensure database tables exist (creates if missing)
    try:
        db_manager.create_tables()
    except Exception as e:
        logger.error(f"Failed to create DB tables: {e}")
        return

    # List of US tickers to process – can be expanded as needed
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"]

    # 1️⃣ Fetch raw statements from yfinance
    fetcher = YFinanceFetcher()
    failed_fetch = fetcher.download_batch(tickers)
    if failed_fetch:
        logger.warning(f"Raw data fetch failed for: {failed_fetch}")
    else:
        logger.info("Raw data fetched for all tickers.")

    # 2️⃣ Clean & transform raw CSVs into silver layer
    cleaner = FinancialCleaner()
    failed_clean = cleaner.clean_batch(tickers)
    if failed_clean:
        logger.warning(f"Data cleaning failed for: {failed_clean}")
    else:
        logger.info("All raw data cleaned into silver layer.")

    # 3️⃣ Load silver data into the PostgreSQL/SQLite database (gold layer)
    loader = DatabaseLoader()
    failed_load = loader.load_batch(tickers)
    if failed_load:
        logger.warning(f"Database load failed for: {failed_load}")
    else:
        logger.info("All ticker data successfully loaded into the DB.")


if __name__ == "__main__":
    main()
