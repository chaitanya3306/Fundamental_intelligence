"""Utility functions for persisting pipeline execution metadata.

The pipeline produces two kinds of rows:

* ``PipelineRun`` – one per execution (UUID, timestamps, overall status).
* ``PipelineCompanyRun`` – one per ticker in that execution (status, freshness info).

Both tables are defined in ``src.database.models`` and are created automatically
by ``db_manager.create_tables()`` because they share the same ``Base``.
"""

from datetime import datetime
from typing import List, Dict, Optional

from src.database.session import db_manager
from src.database.models import (
    PipelineRun,
    PipelineCompanyRun,
    Company,
    FinancialStatement,
)


def _utc_now() -> datetime:
    """Return a timezone‑aware UTC datetime (used for DB columns)."""
    return datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


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
    """Insert a ``PipelineRun`` and its related ``PipelineCompanyRun`` rows.

    ``started_at`` and ``completed_at`` are ISO‑8601 strings produced by the
    pipeline (``utc_now()``).  They are parsed back to ``datetime`` objects for the
    DB columns.
    """
    # Parse ISO‑8601 strings back to datetime objects – SQLAlchemy can store naive
    # datetimes; we keep them in UTC.
    started_dt = datetime.fromisoformat(started_at)
    completed_dt = datetime.fromisoformat(completed_at) if completed_at else None

    session = db_manager.get_session()
    try:
        # ------------------------------------------------------------------
        # Insert the top‑level run record
        # ------------------------------------------------------------------
        run = PipelineRun(
            run_id=run_id,
            started_at=started_dt,
            completed_at=completed_dt,
            overall_status=overall_status,
            failed_stage=failed_stage,
            failure_reason=failure_reason,
            duration_seconds=duration_seconds,
        )
        session.add(run)

        # ------------------------------------------------------------------
        # Insert per‑ticker rows
        # ------------------------------------------------------------------
        for cr in company_rows:
            company_run = PipelineCompanyRun(
                run_id=run_id,
                ticker=cr["ticker"],
                status=cr["status"],
                failed_stage=cr.get("failed_stage"),
                failure_reason=cr.get("failure_reason"),
                last_successful_refresh=cr.get("last_successful_refresh"),
                latest_reporting_period=cr.get("latest_reporting_period"),
                per_statement_status=cr.get("per_statement_status"),
            )
            session.add(company_run)

        session.commit()
    finally:
        session.close()
