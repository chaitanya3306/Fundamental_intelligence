"""Reliability tests for loading Silver financial data into the database."""

import csv
from pathlib import Path

import pytest

from src.database.loader import DatabaseLoader
from src.database.models import Company, FinancialStatement
from src.database.session import db_manager


STATEMENTS = ("income_statement", "balance_sheet", "cashflow")


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Give each test its own temporary SQLite database."""
    db_url = f"sqlite:///{tmp_path / 'loader-test.db'}"
    monkeypatch.setattr(db_manager, "engine_url", db_url, raising=False)
    db_manager.create_tables()
    yield


def write_statement(path: Path, rows: list[dict], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_valid_silver_dataset(folder: Path, revenue: str = "100") -> None:
    """Create the three required Silver CSVs in date-indexed format."""
    write_statement(
        folder / "income_statement.csv",
        [{"date": "2024-12-31", "Total Revenue": revenue, "Net Income": "20"}],
        ["date", "Total Revenue", "Net Income"],
    )
    write_statement(
        folder / "balance_sheet.csv",
        [{"date": "2024-12-31", "Total Assets": "500", "Total Liabilities": "200"}],
        ["date", "Total Assets", "Total Liabilities"],
    )
    write_statement(
        folder / "cashflow.csv",
        [{"date": "2024-12-31", "Free Cash Flow": "15"}],
        ["date", "Free Cash Flow"],
    )


def query_counts(ticker: str) -> tuple[int, int]:
    session = db_manager.get_session()
    try:
        company_count = (
            session.query(Company).filter(Company.ticker == ticker).count()
        )
        observation_count = (
            session.query(FinancialStatement)
            .join(Company)
            .filter(Company.ticker == ticker)
            .count()
        )
        return company_count, observation_count
    finally:
        session.close()


def test_valid_silver_dataset_loads_all_observations(
    tmp_path, monkeypatch, isolated_database
):
    silver_root = tmp_path / "silver"
    write_valid_silver_dataset(silver_root / "LOADCO")
    monkeypatch.setenv("FINANCIAL_SILVER_DIR", str(silver_root))

    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("LOADCO") is True

    company_count, observation_count = query_counts("LOADCO")
    assert company_count == 1
    assert observation_count == 5


def test_reloading_dataset_updates_existing_observations(
    tmp_path, monkeypatch, isolated_database
):
    silver_root = tmp_path / "silver"
    company_folder = silver_root / "RELOADCO"
    write_valid_silver_dataset(company_folder, revenue="100")
    monkeypatch.setenv("FINANCIAL_SILVER_DIR", str(silver_root))
    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("RELOADCO") is True
    write_valid_silver_dataset(company_folder, revenue="125")
    assert loader._load_company_data("RELOADCO") is True

    session = db_manager.get_session()
    try:
        company = session.query(Company).filter_by(ticker="RELOADCO").one()
        revenue_rows = (
            session.query(FinancialStatement)
            .filter_by(
                company_id=company.company_id,
                statement_type="income_statement",
                metric_name="Total Revenue",
            )
            .all()
        )
        assert len(revenue_rows) == 1
        assert revenue_rows[0].value == 125.0
    finally:
        session.close()


def test_invalid_value_rolls_back_company_and_partial_observations(
    tmp_path, monkeypatch, isolated_database
):
    silver_root = tmp_path / "silver"
    company_folder = silver_root / "BROKENCO"
    write_valid_silver_dataset(company_folder)
    # Income statement is processed first; the invalid balance-sheet value then
    # raises during conversion, after some changes have entered the transaction.
    write_statement(
        company_folder / "balance_sheet.csv",
        [{"date": "2024-12-31", "Total Assets": "not-a-number"}],
        ["date", "Total Assets"],
    )
    monkeypatch.setenv("FINANCIAL_SILVER_DIR", str(silver_root))
    loader = DatabaseLoader(silver_dir=str(silver_root))

    assert loader._load_company_data("BROKENCO") is False
    assert query_counts("BROKENCO") == (0, 0)
