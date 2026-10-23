import csv
from pathlib import Path

import pytest

from src.database.loader import DatabaseLoader
from src.database.models import Company, FinancialStatement
from src.database.session import db_manager

@pytest.fixture
def isolated_database(tmp_path):
    """Use a separate temporary SQLite database for each test."""
    original_engine_url = db_manager.engine_url
    db_manager.engine_url = f"sqlite:///{tmp_path / 'loader-test.db'}"
    db_manager.create_tables()

    yield

    # Close the test engine and restore the original configuration.
    # Use the internal attributes of DatabaseSession to clean up.
    if getattr(db_manager, "_engine", None) is not None:
        db_manager._engine.dispose()
    db_manager._engine = None
    db_manager._SessionLocal = None
    db_manager.engine_url = original_engine_url

def write_statement(path: Path, rows: list[dict]) -> None:
    """Write a Silver statement CSV with dates as the index."""
    path.parent.mkdir(parents=True, exist_ok=True)


    fieldnames = list(rows[0].keys())
    date_column = "date"
    metric_columns = [column for column in fieldnames if column != date_column]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[date_column, *metric_columns],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def write_valid_silver_dataset(
    silver_root: Path,
    ticker: str = "TESTCO",
    revenue: str = "100",
) -> None:
    """Create all three required Silver statement files."""
    folder = silver_root / ticker
    folder.mkdir(parents=True, exist_ok=True)

    write_statement(
        folder / "income_statement.csv",
        [
            {
                "date": "2024-12-31",
                "Total Revenue": revenue,
                "Net Income": "25",
            }
        ],
    )

    write_statement(
        folder / "balance_sheet.csv",
        [
            {
                "date": "2024-12-31",
                "Total Assets": "500",
                "Total Liabilities": "200",
            }
        ],
    )

    write_statement(
        folder / "cashflow.csv",
        [
            {
                "date": "2024-12-31",
                "Free Cash Flow": "50",
            }
        ],
    )

def query_counts(ticker: str) -> tuple[int, int]:
    """Return company and financial observation counts for a ticker."""
    session = db_manager.get_session()

    try:
        company_count = (
            session.query(Company)
            .filter(Company.ticker == ticker)
            .count()
        )

        company = (
            session.query(Company)
            .filter(Company.ticker == ticker)
            .first()
        )

        observation_count = 0

        if company is not None:
            observation_count = (
                session.query(FinancialStatement)
                .filter(
                    FinancialStatement.company_id == company.company_id
                )
                .count()
            )

        return company_count, observation_count
    finally:
        session.close()

def test_valid_silver_dataset_loads_all_observations(
    tmp_path, monkeypatch, isolated_database
):
    """A valid dataset loads its company and all five observations."""
    silver_root = tmp_path / "silver"
    write_valid_silver_dataset(silver_root)

    monkeypatch.setenv("FINANCIAL_SILVER_DIR", str(silver_root))
    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is True
    assert query_counts("TESTCO") == (1, 5)

def test_reloading_dataset_updates_existing_observations(
    tmp_path, monkeypatch, isolated_database
):
    """Reloading changed financial data updates rather than duplicates rows."""
    silver_root = tmp_path / "silver"
    write_valid_silver_dataset(silver_root, revenue="100")

    monkeypatch.setenv("FINANCIAL_SILVER_DIR", str(silver_root))
    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is True

    write_valid_silver_dataset(silver_root, revenue="125")

    assert loader._load_company_data("TESTCO") is True

    session = db_manager.get_session()

    try:
        revenue_rows = (
            session.query(FinancialStatement)
            .join(Company)
            .filter(
                Company.ticker == "TESTCO",
                FinancialStatement.statement_type == "income_statement",
                FinancialStatement.metric_name == "Total Revenue",
            )
            .all()
        )

        assert len(revenue_rows) == 1
        assert revenue_rows[0].value == pytest.approx(125.0)
    finally:
        session.close()

    assert query_counts("TESTCO") == (1, 5)

def test_invalid_value_rolls_back_company_and_partial_observations(
    tmp_path, monkeypatch, isolated_database
):
    """A loading error rolls back the company and earlier observations."""
    silver_root = tmp_path / "silver"
    write_valid_silver_dataset(silver_root)

    # The loader processes income_statement before balance_sheet.
    # This invalid value triggers an error after earlier observations
    # have already been processed within the same transaction.
    write_statement(
        silver_root / "TESTCO" / "balance_sheet.csv",
        [
            {
                "date": "2024-12-31",
                "Total Assets": "not-a-number",
                "Total Liabilities": "200",
            }
        ],
    )

    monkeypatch.setenv("FINANCIAL_SILVER_DIR", str(silver_root))
    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is False
    assert query_counts("TESTCO") == (0, 0)
