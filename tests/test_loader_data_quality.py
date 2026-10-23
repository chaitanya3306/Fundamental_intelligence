
import csv
from datetime import date

import pandas as pd
import pytest

from src.database.loader import DatabaseLoader
from src.database.models import Company, FinancialStatement
from src.database.session import db_manager

STATEMENTS = (
    "income_statement",
    "balance_sheet",
    "cashflow",
)


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Give each test its own temporary SQLite database."""
    original_engine_url = db_manager.engine_url

    if getattr(db_manager, "_engine", None) is not None:
        db_manager._engine.dispose()

    db_manager._engine = None
    db_manager._SessionLocal = None
    db_manager.engine_url = f"sqlite:///{tmp_path / 'quality-test.db'}"

    db_manager.create_tables()

    yield

    if getattr(db_manager, "_engine", None) is not None:
        db_manager._engine.dispose()

    db_manager._engine = None
    db_manager._SessionLocal = None
    db_manager.engine_url = original_engine_url


def write_valid_dataset(folder, ticker="TESTCO"):
    """Write valid data for all three required statements."""
    company_folder = folder / ticker
    company_folder.mkdir(parents=True, exist_ok=True)

    datasets = {
        "income_statement": {
            "Total Revenue": [1000.0, 1200.0],
            "Net Income": [100.0, 150.0],
        },
        "balance_sheet": {
            "Total Assets": [5000.0, 5500.0],
            "Total Liabilities": [2000.0, 2100.0],
        },
        "cashflow": {
            "Free Cash Flow": [300.0, 400.0],
        },
    }

    dates = ["2024-03-31", "2024-06-30"]

    for statement, metrics in datasets.items():
        df = pd.DataFrame(metrics, index=dates)
        df.index.name = "date"
        df.to_csv(company_folder / f"{statement}.csv")

    return company_folder


def database_counts(ticker="TESTCO"):
    """Return the company count and its observation count."""
    session = db_manager.get_session()

    try:
        company = (
            session.query(Company)
            .filter(Company.ticker == ticker)
            .first()
        )

        if company is None:
            return 0, 0

        observations = (
            session.query(FinancialStatement)
            .filter(
                FinancialStatement.company_id == company.company_id
            )
            .count()
        )

        return 1, observations
    finally:
        session.close()


def test_invalid_reporting_date_rolls_back_entire_load(
    tmp_path, isolated_database
):
    silver_root = tmp_path / "silver"
    company_folder = write_valid_dataset(silver_root)

    # Replace one valid date with an invalid reporting date.
    df = pd.DataFrame(
        {"Total Revenue": [1000.0]},
        index=["not-a-date"],
    )
    df.index.name = "date"
    df.to_csv(company_folder / "income_statement.csv")

    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is False
    assert database_counts() == (0, 0)


@pytest.mark.parametrize("bad_value", [float("inf"), float("-inf")])
def test_infinite_financial_value_rolls_back_entire_load(
    tmp_path, isolated_database, bad_value
):
    silver_root = tmp_path / "silver"
    company_folder = write_valid_dataset(silver_root)

    df = pd.DataFrame(
        {"Total Revenue": [bad_value]},
        index=["2024-03-31"],
    )
    df.index.name = "date"
    df.to_csv(company_folder / "income_statement.csv")

    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is False
    assert database_counts() == (0, 0)


def test_duplicate_reporting_dates_are_rejected(
    tmp_path, isolated_database
):
    silver_root = tmp_path / "silver"
    company_folder = write_valid_dataset(silver_root)

    # Two rows claim to report the same financial metric on the same date.
    df = pd.DataFrame(
        {"Total Revenue": [1000.0, 1200.0]},
        index=["2024-03-31", "2024-03-31"],
    )
    df.index.name = "date"
    df.to_csv(company_folder / "income_statement.csv")

    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is False
    assert database_counts() == (0, 0)


def test_duplicate_metric_columns_are_rejected(
    tmp_path, isolated_database
):
    silver_root = tmp_path / "silver"
    company_folder = write_valid_dataset(silver_root)

    # Write a CSV with a duplicate metric column name directly.
    path = company_folder / "income_statement.csv"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["date", "Total Revenue", "Total Revenue"]
        )
        writer.writerow(
            ["2024-03-31", "1000", "1100"]
        )

    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is False
    assert database_counts() == (0, 0)


def test_missing_financial_values_remain_allowed(
    tmp_path, isolated_database
):
    silver_root = tmp_path / "silver"
    company_folder = write_valid_dataset(silver_root)

    # One missing metric should remain missing, not become zero.
    df = pd.DataFrame(
        {
            "Total Revenue": [1000.0, float("nan")],
            "Net Income": [100.0, 150.0],
        },
        index=["2024-03-31", "2024-06-30"],
    )
    df.index.name = "date"
    df.to_csv(company_folder / "income_statement.csv")

    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is True

    session = db_manager.get_session()

    try:
        company = (
            session.query(Company)
            .filter(Company.ticker == "TESTCO")
            .one()
        )

        revenue_rows = (
            session.query(FinancialStatement)
            .filter(
                FinancialStatement.company_id == company.company_id,
                FinancialStatement.statement_type == "income_statement",
                FinancialStatement.metric_name == "Total Revenue",
            )
            .all()
        )

        # The missing value is skipped, while the valid value is retained.
        assert len(revenue_rows) == 1
        assert revenue_rows[0].date == date(2024, 3, 31)
        assert revenue_rows[0].value == pytest.approx(1000.0)
    finally:
        session.close()

def test_metric_headers_with_surrounding_whitespace_are_rejected(
    tmp_path, isolated_database
):
    silver_root = tmp_path / "silver"
    company_folder = write_valid_dataset(silver_root)

    path = company_folder / "income_statement.csv"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["date", "Total Revenue", " Total Revenue "]
        )
        writer.writerow(
            ["2024-03-31", "1000", "1100"]
        )

    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is False
    assert database_counts() == (0, 0)


def test_blank_metric_header_is_rejected(
    tmp_path, isolated_database
):
    silver_root = tmp_path / "silver"
    company_folder = write_valid_dataset(silver_root)

    path = company_folder / "income_statement.csv"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "Total Revenue", ""])
        writer.writerow(["2024-03-31", "1000", "200"])

    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("TESTCO") is False
    assert database_counts() == (0, 0)
