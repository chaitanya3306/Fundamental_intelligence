"""add financial observation lineage

Revision ID: efbad29c7a3c
Revises: a844f029391c
Create Date: 2026-10-27 18:47:42.662114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "efbad29c7a3c"
down_revision: Union[str, None] = "a844f029391c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # 1. Create pipeline run audit tables
    # ---------------------------------------------------------

    op.create_table(
        "pipeline_runs",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overall_status", sa.String(), nullable=False),
        sa.Column("failed_stage", sa.String(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("run_id"),
    )

    op.create_table(
        "pipeline_company_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("failed_stage", sa.String(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "last_successful_refresh",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "latest_reporting_period",
            sa.Date(),
            nullable=True,
        ),
        sa.Column("per_statement_status", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["pipeline_runs.run_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            "ticker",
            name="uq_pipeline_company_run",
        ),
    )

    # ---------------------------------------------------------
    # 2. Add lineage columns to financial statements
    # ---------------------------------------------------------
    # Initially nullable because existing records already exist
    # and do not have lineage metadata.

    op.add_column(
        "financial_statements",
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "financial_statements",
        sa.Column(
            "ingestion_run_id",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "financial_statements",
        sa.Column(
            "source",
            sa.String(),
            nullable=True,
        ),
    )

    # ---------------------------------------------------------
    # 3. Backfill existing records
    # ---------------------------------------------------------
    # Historical ingestion timestamps are unavailable.
    # CURRENT_TIMESTAMP records the migration time, not the
    # actual historical ingestion time.
    #
    # Existing records in this project were fetched from
    # Yahoo Finance, so their source is recorded accordingly.
    #
    # ingestion_run_id remains NULL for legacy records because
    # their original pipeline run IDs are unknown.

    op.execute(
        """
        UPDATE financial_statements
        SET ingested_at = CURRENT_TIMESTAMP
        WHERE ingested_at IS NULL
        """
    )

    op.execute(
        """
        UPDATE financial_statements
        SET source = 'yfinance'
        WHERE source IS NULL
        """
    )

    # ---------------------------------------------------------
    # 4. Enforce required lineage fields
    # ---------------------------------------------------------

    op.alter_column(
        "financial_statements",
        "ingested_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    op.alter_column(
        "financial_statements",
        "source",
        existing_type=sa.String(),
        nullable=False,
    )

    # ---------------------------------------------------------
    # 5. Add foreign key for ingestion run lineage
    # ---------------------------------------------------------

    op.create_foreign_key(
        "fk_financial_statements_ingestion_run_id_pipeline_runs",
        "financial_statements",
        "pipeline_runs",
        ["ingestion_run_id"],
        ["run_id"],
    )


def downgrade() -> None:
    # ---------------------------------------------------------
    # 1. Remove foreign key
    # ---------------------------------------------------------

    op.drop_constraint(
        "fk_financial_statements_ingestion_run_id_pipeline_runs",
        "financial_statements",
        type_="foreignkey",
    )

    # ---------------------------------------------------------
    # 2. Remove lineage columns
    # ---------------------------------------------------------

    op.drop_column("financial_statements", "source")
    op.drop_column("financial_statements", "ingestion_run_id")
    op.drop_column("financial_statements", "ingested_at")

    # ---------------------------------------------------------
    # 3. Remove audit tables
    # ---------------------------------------------------------

    op.drop_table("pipeline_company_runs")
    op.drop_table("pipeline_runs")