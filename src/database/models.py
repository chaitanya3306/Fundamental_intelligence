from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

from sqlalchemy import Column, Date, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint, JSON, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime,timezone
Base=declarative_base()


# this will store the static info about the company
class Company(Base):
    __tablename__="companies"
    company_id=Column(Integer,primary_key=True,autoincrement=True)
    ticker=Column(String,unique=True,nullable=False,index=True)
    sector = Column(String) # e.g., "IT Services"
    industry = Column(String) # e.g., "Software"
    shares_outstanding=Column(Float,nullable=True)
    current_price=Column(Float,nullable=True)
    last_updated = Column(DateTime, default=datetime.now(), onupdate=datetime.utcnow, nullable=False)

    #relationships:
    # this allow us to get the data from another table in pythonic way like company.statements
    statements=relationship("FinancialStatement",back_populates="company")

# it stores the actual variable data or numbers
class FinancialStatement(Base):
    __tablename__ = 'financial_statements'


    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "date",
            "statement_type",
            "metric_name",
            name="uq_financial_statement_observation",
        ),
    )



    statement_id=Column(Integer,primary_key=True,autoincrement=True)
    company_id=Column(Integer,ForeignKey('companies.company_id'))
    date=Column(Date,nullable=False,index=True)
    statement_type=Column(String,nullable=False)
    metric_name=Column(String,nullable=False)
    value=Column(Float,nullable=False)

    ingested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ingestion_run_id = Column(
        String,
        ForeignKey("pipeline_runs.run_id"),
        nullable=True,
    )
    source = Column(String, nullable=False, default="yfinance")

    company=relationship("Company", back_populates="statements")


    @hybrid_property
    def company_ticker(self):
        """Return the ticker symbol of the related company.

        This hybrid property allows ORM queries such as
        ``filter_by(company_ticker='BADCO')`` to work by generating a subquery
        that selects the ticker from the ``companies`` table based on the
        ``company_id`` foreign key.
        """
        return self.company.ticker if self.company else None

    @company_ticker.expression
    def company_ticker(cls):
        return (
            select(Company.ticker)
            .where(Company.company_id == cls.company_id)
            .scalar_subquery()
        )

# ----------------------------------------------------------------------
#  Pipeline‑run audit tables
# ----------------------------------------------------------------------
class PipelineRun(Base):
    """
    One row per invocation of ``run_pipeline``.
    Stores high‑level status and timestamps.
    """
    __tablename__ = "pipeline_runs"

    run_id = Column(String, primary_key=True)  # UUID generated in run_pipeline
    started_at = Column(DateTime(timezone=True), nullable=False)  # utc_now()
    completed_at = Column(DateTime(timezone=True), nullable=True)  # set in finally block
    overall_status = Column(String, nullable=False)  # success / partial_failure / failure
    failed_stage = Column(String, nullable=True)  # fetch / clean / load  (null if overall_status!=failure)
    failure_reason = Column(Text, nullable=True)  # exception message if any
    duration_seconds = Column(Float, nullable=True)  # total wall‑clock time

    # One‑to‑many relationship – convenient for ORM queries
    company_runs = relationship(
        "PipelineCompanyRun",
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
    )

class PipelineCompanyRun(Base):
    """
    One row per ticker inside a pipeline run.
    Captures the per‑ticker outcome and freshness information.
    """
    __tablename__ = "pipeline_company_runs"

    __table_args__ = (
        UniqueConstraint("run_id", "ticker", name="uq_pipeline_company_run"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("pipeline_runs.run_id"), nullable=False)
    ticker = Column(String, nullable=False)  # e.g. "AAPL"

    # ---------- outcome ----------
    status = Column(String, nullable=False)  # success / fetch_failed / clean_failed / load_failed
    failed_stage = Column(String, nullable=True)  # fetch / clean / load (only when status != success)
    failure_reason = Column(Text, nullable=True)  # optional free‑form message

    # ---------- freshness ----------
    last_successful_refresh = Column(DateTime(timezone=True), nullable=True)  # UTC when this ticker succeeded
    latest_reporting_period = Column(Date, nullable=True)  # MAX(date) that now lives in FinancialStatement

    # Optional JSON blob with per‑statement status (income_statement, balance_sheet, cashflow)
    per_statement_status = Column(JSON, nullable=True)

    # ORM back‑ref
    pipeline_run = relationship("PipelineRun", back_populates="company_runs")

