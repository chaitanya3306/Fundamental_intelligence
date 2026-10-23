
from datetime import date

import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError

from src.database.models import Company, FinancialStatement
from src.database.session import db_manager
from src.database.loader import DatabaseLoader


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """Give every test its own temporary database."""
    db_url = f"sqlite:///{tmp_path / 'test.db'}"

    monkeypatch.setattr(db_manager, "engine_url", db_url)
    db_manager.create_tables()

    yield

    # Close the temporary database connection after the test.
    if db_manager._engine is not None:
        db_manager._engine.dispose()
        db_manager._engine = None
        db_manager._SessionLocal = None


def create_company(session, ticker="TEST"):
    """Create a company and return its database ID."""
    company = Company(ticker=ticker)
    session.add(company)
    session.flush()
    return company.company_id


def test_duplicate_observation_is_rejected(fresh_db):
    """The database must reject duplicate financial observations."""
    session = db_manager.get_session()

    try:
        company_id = create_company(session)

        observation = FinancialStatement(
            company_id=company_id,
            date=date(2024, 3, 31),
            statement_type="income_statement",
            metric_name="Total Revenue",
            value=1000.0,
        )

        session.add(observation)
        session.commit()

        duplicate = FinancialStatement(
            company_id=company_id,
            date=date(2024, 3, 31),
            statement_type="income_statement",
            metric_name="Total Revenue",
            value=2000.0,
        )

        session.add(duplicate)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

    finally:
        session.close()


def test_different_metrics_are_allowed(fresh_db):
    """Different metrics for the same company and date are valid."""
    session = db_manager.get_session()

    try:
        company_id = create_company(session)

        session.add_all([
            FinancialStatement(
                company_id=company_id,
                date=date(2024, 3, 31),
                statement_type="income_statement",
                metric_name="Total Revenue",
                value=1000.0,
            ),
            FinancialStatement(
                company_id=company_id,
                date=date(2024, 3, 31),
                statement_type="income_statement",
                metric_name="Net Income",
                value=200.0,
            ),
        ])

        session.commit()

        count = session.query(FinancialStatement).count()
        assert count == 2

    finally:
        session.close()


def test_same_metric_for_different_dates_is_allowed(fresh_db):
    """The same metric can have observations for different periods."""
    session = db_manager.get_session()

    try:
        company_id = create_company(session)

        session.add_all([
            FinancialStatement(
                company_id=company_id,
                date=date(2024, 3, 31),
                statement_type="income_statement",
                metric_name="Total Revenue",
                value=1000.0,
            ),
            FinancialStatement(
                company_id=company_id,
                date=date(2024, 6, 30),
                statement_type="income_statement",
                metric_name="Total Revenue",
                value=1200.0,
            ),
        ])

        session.commit()

        count = session.query(FinancialStatement).count()
        assert count == 2

    finally:
        session.close()


def test_loading_same_data_twice_does_not_duplicate_rows(
    fresh_db, tmp_path, monkeypatch
):
    """Repeated pipeline loads update existing observations instead of duplicating them."""
    silver_dir = tmp_path / "silver"
    company_dir = silver_dir / "TEST"
    company_dir.mkdir(parents=True)

    # The loader expects reporting dates as rows and metrics as columns.
    pd.DataFrame(
        {"Total Revenue": [1000.0]},
        index=["2024-03-31"],
    ).to_csv(company_dir / "income_statement.csv")

    pd.DataFrame(
        {"Total Assets": [5000.0]},
        index=["2024-03-31"],
    ).to_csv(company_dir / "balance_sheet.csv")

    pd.DataFrame(
        {"Free Cash Flow": [300.0]},
        index=["2024-03-31"],
    ).to_csv(company_dir / "cashflow.csv")

    monkeypatch.setenv("FINANCIAL_SILVER_DIR", str(silver_dir))
    loader = DatabaseLoader()

    # First load inserts the observations.
    assert loader.load_batch(["TEST"]) == []

    # Second load should update the existing observations.
    assert loader.load_batch(["TEST"]) == []

    session = db_manager.get_session()

    try:
        company = session.query(Company).filter_by(ticker="TEST").one()

        observations = (
            session.query(FinancialStatement)
            .filter_by(company_id=company.company_id)
            .all()
        )

        # Three statements, one observation per statement.
        assert len(observations) == 3

        revenue = (
            session.query(FinancialStatement)
            .filter_by(
                company_id=company.company_id,
                statement_type="income_statement",
                metric_name="Total Revenue",
            )
            .one()
        )

        assert revenue.value == 1000.0

    finally:
        session.close()



def write_valid_silver_files(company_dir):
    """Create three valid Silver statement CSV files."""
    pd.DataFrame(
        {"Total Revenue": [1000.0]},
        index=["2024-03-31"],
    ).to_csv(company_dir / "income_statement.csv")

    pd.DataFrame(
        {"Total Assets": [5000.0]},
        index=["2024-03-31"],
    ).to_csv(company_dir / "balance_sheet.csv")

    pd.DataFrame(
        {"Free Cash Flow": [300.0]},
        index=["2024-03-31"],
    ).to_csv(company_dir / "cashflow.csv")


def test_empty_required_statement_rolls_back_entire_load(
    fresh_db, tmp_path
):
    silver_dir = tmp_path / "silver"
    company_dir = silver_dir / "TEST"
    company_dir.mkdir(parents=True)

    write_valid_silver_files(company_dir)

    # Replace the balance sheet with a CSV containing no data rows.
    pd.DataFrame(
        columns=["Total Assets"]
    ).to_csv(company_dir / "balance_sheet.csv")

    loader = DatabaseLoader(silver_dir=str(silver_dir))

    assert loader.load_batch(["TEST"]) == ["TEST"]

    session = db_manager.get_session()
    try:
        assert session.query(Company).filter_by(ticker="TEST").count() == 0
        assert session.query(FinancialStatement).count() == 0
    finally:
        session.close()


def test_all_missing_statement_rolls_back_entire_load(
    fresh_db, tmp_path
):
    silver_dir = tmp_path / "silver"
    company_dir = silver_dir / "TEST"
    company_dir.mkdir(parents=True)

    write_valid_silver_files(company_dir)

    # The file has a row, but its financial value is missing.
    pd.DataFrame(
        {"Total Assets": [float("nan")]},
        index=["2024-03-31"],
    ).to_csv(company_dir / "balance_sheet.csv")

    loader = DatabaseLoader(silver_dir=str(silver_dir))

    assert loader.load_batch(["TEST"]) == ["TEST"]

    session = db_manager.get_session()
    try:
        assert session.query(Company).filter_by(ticker="TEST").count() == 0
        assert session.query(FinancialStatement).count() == 0
    finally:
        session.close()


def test_failure_in_last_statement_rolls_back_earlier_statements(
    fresh_db, tmp_path
):
    silver_dir = tmp_path / "silver"
    company_dir = silver_dir / "TEST"
    company_dir.mkdir(parents=True)

    write_valid_silver_files(company_dir)

    # Income statement and balance sheet are valid; cash flow is empty.
    pd.DataFrame(
        columns=["Free Cash Flow"]
    ).to_csv(company_dir / "cashflow.csv")

    loader = DatabaseLoader(silver_dir=str(silver_dir))

    assert loader.load_batch(["TEST"]) == ["TEST"]

    session = db_manager.get_session()
    try:
        assert session.query(Company).filter_by(ticker="TEST").count() == 0
        assert session.query(FinancialStatement).count() == 0
    finally:
        session.close()
