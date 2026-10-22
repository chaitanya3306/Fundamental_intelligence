# ======================================================================
#  Test suite for FinSight AI’s data‑pipeline:
#  * validation before cleaning
#  * preservation of true missing values (NaN)
#  * accurate failure reporting
#
#  Run with:
#      pytest -q
#
#  Requirements:
#      - pandas
#      - pytest
#
#  All temporary files are created under the pytest ``tmp_path`` fixture,
#  so the real repository data is never modified.
# ======================================================================

import csv
import pathlib

import pandas as pd
import pytest

# ----------------------------------------------------------------------
#  Project imports – these are the classes we are testing.
# ----------------------------------------------------------------------
from src.data_cleaning.cleaner import FinancialCleaner
from src.data_validation.validator import FinancialValidator
from src.database.loader import DatabaseLoader
from src.database.session import db_manager


# ----------------------------------------------------------------------
# Helper to write a minimal CSV file.
# ----------------------------------------------------------------------
def write_csv(path: pathlib.Path, rows: list[dict], header: list[str]) -> None:
    """
    Write *rows* (list of dicts) to *path* using *header* as the column list.
    The first column is the metric name; subsequent columns are dates.
    This matches the format produced by ``yfinance`` (metric rows, date columns).
    """
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ----------------------------------------------------------------------
# Fixture: replace the production SQLite / Postgres DB with an in‑memory DB
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """
    For every test we spin up a brand‑new SQLite database located inside
    ``tmp_path`` and point the ``db_manager`` to it.  After the test
    finishes the file is automatically deleted.
    """
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setattr(db_manager, "engine_url", db_url, raising=False)
    db_manager.create_tables()
    yield
    # No explicit teardown needed – the temporary file disappears with tmp_path.


# ======================================================================
#  1️⃣  Test: a genuine zero stays zero after cleaning.
# ======================================================================
def test_zero_remains_zero(tmp_path):
    raw_dir = tmp_path / "raw" / "ZEROCO"
    raw_dir.mkdir(parents=True)

    # CSV layout: metric as first column, date as second column
    write_csv(
        raw_dir / "income_statement.csv",
        rows=[{"Metric": "Total Revenue", "2024-01-01": "0"}],
        header=["Metric", "2024-01-01"],
    )
    write_csv(
        raw_dir / "balance_sheet.csv",
        rows=[
            {"Metric": "Total Assets", "2024-01-01": "10"},
            {"Metric": "Total Liabilities Net Minority Interest", "2024-01-01": "5"},
        ],
        header=["Metric", "2024-01-01"],
    )
    write_csv(
        raw_dir / "cashflow.csv",
        rows=[{"Metric": "Free Cash Flow", "2024-01-01": "2"}],
        header=["Metric", "2024-01-01"],
    )

    cleaner = FinancialCleaner(raw_dir=str(tmp_path / "raw"), silver_dir=str(tmp_path / "silver"))
    # clean_batch should return an empty list – no failures
    assert cleaner.clean_batch(["ZEROCO"]) == []

    # Verify the cleaned CSV still holds a numeric zero (not NaN)
    silver_file = tmp_path / "silver" / "ZEROCO" / "income_statement.csv"
    df = pd.read_csv(silver_file, index_col=0)
    # After cleaning the index is the date, columns are metrics
    assert df.iloc[0, 0] == 0


# ======================================================================
#  2️⃣  Test: missing numeric value stays missing (NaN) through cleaning.
# ======================================================================
def test_missing_value_preserved(tmp_path):
    raw_dir = tmp_path / "raw" / "MISSCO"
    raw_dir.mkdir(parents=True)

    write_csv(
        raw_dir / "income_statement.csv",
        rows=[
            {"Metric": "Total Revenue", "2024-01-01": "100", "2024-04-01": ""},
        ],
        header=["Metric", "2024-01-01", "2024-04-01"],
    )
    # Minimal valid balance_sheet & cashflow
    write_csv(
        raw_dir / "balance_sheet.csv",
        rows=[
            {"Metric": "Total Assets", "2024-01-01": "10"},
            {"Metric": "Total Liabilities Net Minority Interest", "2024-01-01": "5"},
        ],
        header=["Metric", "2024-01-01"],
    )
    write_csv(
        raw_dir / "cashflow.csv",
        rows=[{"Metric": "Free Cash Flow", "2024-01-01": "2"}],
        header=["Metric", "2024-01-01"],
    )

    cleaner = FinancialCleaner(raw_dir=str(tmp_path / "raw"), silver_dir=str(tmp_path / "silver"))
    assert cleaner.clean_batch(["MISSCO"]) == []

    silver_file = tmp_path / "silver" / "MISSCO" / "income_statement.csv"
    df = pd.read_csv(silver_file, index_col=0)
    # Silver-layer rows are reporting periods and missing financial values stay missing.
    assert pd.isna(df.loc["2024-04-01", "Total Revenue"])


# ======================================================================
#  3️⃣  Test: an empty raw statement file is rejected by the validator.
# ======================================================================
def test_empty_file_is_rejected(tmp_path):
    raw_dir = tmp_path / "raw" / "EMPTYCO"
    raw_dir.mkdir(parents=True)

    # Empty file (0 bytes)
    (raw_dir / "income_statement.csv").touch()

    # Provide valid other statements
    write_csv(
        raw_dir / "balance_sheet.csv",
        rows=[{"Metric": "Total Assets", "2024-01-01": "1"}],
        header=["Metric", "2024-01-01"],
    )
    write_csv(
        raw_dir / "cashflow.csv",
        rows=[{"Metric": "Free Cash Flow", "2024-01-01": "1"}],
        header=["Metric", "2024-01-01"],
    )

    validator = FinancialValidator()
    failures = validator.validate_data_folder(str(raw_dir))
    assert any("income_statement.csv" in p for p in failures)


# ======================================================================
#  4️⃣  Test: validation failure prevents that statement from being loaded.
# ======================================================================
def test_validation_failure_blocks_db_load(tmp_path):
    raw_dir = tmp_path / "raw" / "BADCO"
    raw_dir.mkdir(parents=True)

    # Valid income_statement
    write_csv(
        raw_dir / "income_statement.csv",
        rows=[{"Metric": "Total Revenue", "2024-01-01": "50"}],
        header=["Metric", "2024-01-01"],
    )
    # Invalid (empty) balance_sheet
    (raw_dir / "balance_sheet.csv").touch()
    # Valid cashflow
    write_csv(
        raw_dir / "cashflow.csv",
        rows=[{"Metric": "Free Cash Flow", "2024-01-01": "5"}],
        header=["Metric", "2024-01-01"],
    )

    cleaner = FinancialCleaner(raw_dir=str(tmp_path / "raw"), silver_dir=str(tmp_path / "silver"))
    assert cleaner.clean_batch(["BADCO"]) == []

    loader = DatabaseLoader()
    loader.load_batch(["BADCO"])

    session = db_manager.get_session()
    count = (
        session.query(DatabaseLoader.model.FinancialStatement)
        .filter_by(company_ticker="BADCO")
        .count()
    )
    session.close()
    assert count == 2


# ======================================================================
#  5️⃣  Test: a ticker with some statements missing still processes the good ones.
# ======================================================================
def test_partial_success_still_processed(tmp_path):
    raw_dir = tmp_path / "raw" / "PARTCO"
    raw_dir.mkdir(parents=True)

    write_csv(
        raw_dir / "income_statement.csv",
        rows=[{"Metric": "Total Revenue", "2024-01-01": "200"}],
        header=["Metric", "2024-01-01"],
    )
    # No balance_sheet file
    write_csv(
        raw_dir / "cashflow.csv",
        rows=[{"Metric": "Free Cash Flow", "2024-01-01": "20"}],
        header=["Metric", "2024-01-01"],
    )

    cleaner = FinancialCleaner(raw_dir=str(tmp_path / "raw"), silver_dir=str(tmp_path / "silver"))
    assert cleaner.clean_batch(["PARTCO"]) == []

    silver_folder = tmp_path / "silver" / "PARTCO"
    silver_files = sorted(p.name for p in silver_folder.iterdir())
    assert silver_files == ["cashflow.csv", "income_statement.csv"]


# ======================================================================
#  6️⃣  Test: pipeline reports a ticker as failed when *all* statements are invalid.
# ======================================================================
def test_pipeline_failure_reporting(tmp_path):
    raw_dir = tmp_path / "raw" / "FAILCO"
    raw_dir.mkdir(parents=True)

    # Create three empty CSVs
    for name in ("income_statement.csv", "balance_sheet.csv", "cashflow.csv"):
        (raw_dir / name).touch()

    cleaner = FinancialCleaner(raw_dir=str(tmp_path / "raw"), silver_dir=str(tmp_path / "silver"))
    failures = cleaner.clean_batch(["FAILCO"])
    assert failures == ["FAILCO"]
