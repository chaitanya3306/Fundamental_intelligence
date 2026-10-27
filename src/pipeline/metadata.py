"""Utility functions for persisting pipeline execution metadata.

The pipeline produces two kinds of rows:

* ``PipelineRun`` – one per execution (UUID, timestamps, overall status).
* ``PipelineCompanyRun`` – one per ticker in that execution (status, freshness info).

The parent PipelineRun record must be created before financial statements are
loaded because FinancialStatement.ingestion_run_id references PipelineRun.run_id.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional

from src.database.session import db_manager
from src.database.models import (
    PipelineRun,
    PipelineCompanyRun,
)


def _utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def start_pipeline_run(
    run_id: str,
    started_at: str,
) -> None:
    """Create the parent PipelineRun record before ingestion begins."""

    started_dt = datetime.fromisoformat(started_at)

    session = db_manager.get_session()

    try:
        run = PipelineRun(
            run_id=run_id,
            started_at=started_dt,
            overall_status="running",
        )

        session.add(run)
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def record_pipeline_run(
    run_id: str,
    started_at: str,
    completed_at: str,
    overall_status: str,
    failed_stage: Optional[str],
    failure_reason: Optional[str],
    duration_seconds: float,
    company_rows: List[Dict],
) -> None:
    """Finalize an existing PipelineRun and persist company-level audit rows.

    ``started_at`` and ``completed_at`` are ISO-8601 strings produced by the
    pipeline. They are parsed back into datetime objects for the DB columns.
    """

    started_dt = datetime.fromisoformat(started_at)
    completed_dt = (
        datetime.fromisoformat(completed_at)
        if completed_at
        else None
    )

    session = db_manager.get_session()

    try:
        # --------------------------------------------------------------
        # Update the existing parent PipelineRun record
        # --------------------------------------------------------------
        run = (
            session.query(PipelineRun)
            .filter(PipelineRun.run_id == run_id)
            .one()
        )

        run.started_at = started_dt
        run.completed_at = completed_dt
        run.overall_status = overall_status
        run.failed_stage = failed_stage
        run.failure_reason = failure_reason
        run.duration_seconds = duration_seconds

        # --------------------------------------------------------------
        # Insert per-ticker PipelineCompanyRun records
        # --------------------------------------------------------------
        for cr in company_rows:
            company_run = PipelineCompanyRun(
                run_id=run_id,
                ticker=cr["ticker"],
                status=cr["status"],
                failed_stage=cr.get("failed_stage"),
                failure_reason=cr.get("failure_reason"),
                last_successful_refresh=cr.get(
                    "last_successful_refresh"
                ),
                latest_reporting_period=cr.get(
                    "latest_reporting_period"
                ),
                per_statement_status=cr.get(
                    "per_statement_status"
                ),
            )

            session.add(company_run)

        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()