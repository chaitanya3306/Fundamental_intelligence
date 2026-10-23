"""Run and monitor the raw -> Silver -> database pipeline."""

import logging
import time
from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4

from src.data_ingestion.fetch_basics import YFinanceFetcher
from src.data_cleaning.cleaner import FinancialCleaner
from src.database.loader import DatabaseLoader

logger = logging.getLogger(__name__)

DEFAULT_TICKERS = (
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "NVDA",
)


def utc_now() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def run_pipeline(tickers: Iterable[str] = DEFAULT_TICKERS) -> dict:
    """Run the pipeline and return a structured execution report."""

    run_id = str(uuid4())
    started_at = utc_now()
    pipeline_start = time.perf_counter()

    requested = list(dict.fromkeys(tickers))

    result = {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": None,
        "status": "running",
        "requested": requested,
        "fetch_failed": [],
        "clean_failed": [],
        "load_failed": [],
        "stage_durations_seconds": {
            "fetch": 0.0,
            "clean": 0.0,
            "load": 0.0,
        },
        "duration_seconds": 0.0,
    }

    logger.info(
        "Pipeline started: run_id=%s requested_tickers=%s",
        run_id,
        requested,
    )

    try:
        if not requested:
            logger.warning(
                "Pipeline received no tickers: run_id=%s",
                run_id,
            )
            result["status"] = "success"
            return result

        # Stage 1: Fetch raw financial data.
        stage_start = time.perf_counter()

        try:
            fetcher = YFinanceFetcher()
            result["fetch_failed"] = fetcher.download_batch(requested) or []
        except Exception:
            logger.exception(
                "Ingestion stage failed unexpectedly: run_id=%s",
                run_id,
            )
            result["fetch_failed"] = requested.copy()

        result["stage_durations_seconds"]["fetch"] = round(
            time.perf_counter() - stage_start, 4
        )

        fetch_failed = set(result["fetch_failed"])
        fetched = [
            ticker for ticker in requested
            if ticker not in fetch_failed
        ]

        logger.info(
            "Ingestion finished: run_id=%s succeeded=%d failed=%d",
            run_id,
            len(fetched),
            len(result["fetch_failed"]),
        )

        # Stage 2: Clean successful fetches only.
        stage_start = time.perf_counter()

        try:
            cleaner = FinancialCleaner()
            result["clean_failed"] = cleaner.clean_batch(fetched) or []
        except Exception:
            logger.exception(
                "Cleaning stage failed unexpectedly: run_id=%s",
                run_id,
            )
            result["clean_failed"] = fetched.copy()

        result["stage_durations_seconds"]["clean"] = round(
            time.perf_counter() - stage_start, 4
        )

        clean_failed = set(result["clean_failed"])
        cleaned = [
            ticker for ticker in fetched
            if ticker not in clean_failed
        ]

        logger.info(
            "Cleaning finished: run_id=%s succeeded=%d failed=%d",
            run_id,
            len(cleaned),
            len(result["clean_failed"]),
        )

        # Stage 3: Load successfully cleaned data only.
        stage_start = time.perf_counter()

        try:
            loader = DatabaseLoader()
            result["load_failed"] = loader.load_batch(cleaned) or []
        except Exception:
            logger.exception(
                "Database loading stage failed unexpectedly: run_id=%s",
                run_id,
            )
            result["load_failed"] = cleaned.copy()

        result["stage_durations_seconds"]["load"] = round(
            time.perf_counter() - stage_start, 4
        )

        logger.info(
            "Database loading finished: run_id=%s attempted=%d failed=%d",
            run_id,
            len(cleaned),
            len(result["load_failed"]),
        )

        failed_tickers = (
                set(result["fetch_failed"])
                | set(result["clean_failed"])
                | set(result["load_failed"])
        )

        if not failed_tickers:
            result["status"] = "success"
        elif set(requested).issubset(failed_tickers):
            result["status"] = "failure"
        else:
            result["status"] = "partial_failure"

        return result

    finally:
        result["completed_at"] = utc_now()
        result["duration_seconds"] = round(
            time.perf_counter() - pipeline_start, 4
        )
        logger.info(
            "Pipeline completed: run_id=%s status=%s duration_seconds=%.4f",
            run_id,
            result["status"],
            result["duration_seconds"],
        )
        logger.info("Pipeline execution report: %s", result)

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    result = run_pipeline()

    if result["status"] == "success":
        logger.info("All requested tickers processed successfully.")
    else:
        logger.error(
            "Pipeline finished with status=%s. Report: %s",
            result["status"],
            result,
        )


if __name__ == "__main__":
    main()