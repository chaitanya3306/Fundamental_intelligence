"""Run the raw -> Silver -> database pipeline with stage-level failure gates."""
import logging
from typing import Iterable, List

from src.data_ingestion.fetch_basics import YFinanceFetcher
from src.data_cleaning.cleaner import FinancialCleaner
from src.database.loader import DatabaseLoader

logger = logging.getLogger(__name__)
DEFAULT_TICKERS = ("AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA")


def run_pipeline(tickers: Iterable[str] = DEFAULT_TICKERS) -> dict:
    """Run each stage only for tickers that succeeded in the preceding stage.

    Returning per-stage failures makes the run observable and prevents stale
    raw/Silver files for a failed refresh from being loaded as if they were fresh.
    """
    requested = list(dict.fromkeys(tickers))
    if not requested:
        return {"requested": [], "fetch_failed": [], "clean_failed": [], "load_failed": []}

    fetcher = YFinanceFetcher()
    fetch_failed = fetcher.download_batch(requested)
    fetched = [ticker for ticker in requested if ticker not in set(fetch_failed)]

    cleaner = FinancialCleaner()
    clean_failed = cleaner.clean_batch(fetched)
    cleaned = [ticker for ticker in fetched if ticker not in set(clean_failed)]

    loader = DatabaseLoader()
    load_failed = loader.load_batch(cleaned)

    result = {
        "requested": requested,
        "fetch_failed": fetch_failed,
        "clean_failed": clean_failed,
        "load_failed": load_failed,
    }
    logger.info("Pipeline summary: %s", result)
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    result = run_pipeline()
    failures = result["fetch_failed"] + result["clean_failed"] + result["load_failed"]
    if failures:
        logger.error("Pipeline completed with failures: %s", result)
    else:
        logger.info("Pipeline completed successfully for all requested tickers.")


if __name__ == "__main__":
    main()
