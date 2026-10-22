import pandas as pd

from src.data_validation.validator import FinancialValidator


def create_valid_statements(folder):
    """Create valid sample CSV files for all three statements."""

    income_statement = pd.DataFrame(
        {
            "2025-12-31": [1000, 200],
            "2024-12-31": [900, 180],
        },
        index=["Total Revenue", "Net Income"],
    )

    balance_sheet = pd.DataFrame(
        {
            "2025-12-31": [5000, 2000],
            "2024-12-31": [4500, 1800],
        },
        index=[
            "Total Assets",
            "Total Liabilities Net Minority Interest",
        ],
    )

    cashflow = pd.DataFrame(
        {
            "2025-12-31": [300],
            "2024-12-31": [250],
        },
        index=["Free Cash Flow"],
    )

    income_statement.to_csv(folder / "income_statement.csv")
    balance_sheet.to_csv(folder / "balance_sheet.csv")
    cashflow.to_csv(folder / "cashflow.csv")


def test_all_valid_statements_pass(tmp_path):
    create_valid_statements(tmp_path)

    validator = FinancialValidator()

    failures = validator.validate_data_folder(str(tmp_path))

    assert failures == []


def test_missing_statement_is_reported(tmp_path):
    create_valid_statements(tmp_path)

    (tmp_path / "balance_sheet.csv").unlink()

    validator = FinancialValidator()

    failures = validator.validate_data_folder(str(tmp_path))

    assert str(tmp_path / "balance_sheet.csv") in failures


def test_empty_statement_fails(tmp_path):
    create_valid_statements(tmp_path)

    (tmp_path / "income_statement.csv").write_text(
        "",
        encoding="utf-8",
    )

    validator = FinancialValidator()

    assert not validator.validate_file(
        str(tmp_path / "income_statement.csv"),
        "income_statement",
    )


def test_missing_required_metric_fails(tmp_path):
    file_path = tmp_path / "income_statement.csv"

    df = pd.DataFrame(
        {"2025-12-31": [200]},
        index=["Net Income"],
    )

    df.to_csv(file_path)

    validator = FinancialValidator()

    assert not validator.validate_file(
        str(file_path),
        "income_statement",
    )


def test_non_numeric_revenue_fails(tmp_path):
    file_path = tmp_path / "income_statement.csv"

    df = pd.DataFrame(
        {
            "2025-12-31": ["abc"],
            "2024-12-31": ["900"],
        },
        index=["Total Revenue"],
    )

    df.to_csv(file_path)

    validator = FinancialValidator()

    assert not validator.validate_file(
        str(file_path),
        "income_statement",
    )


def test_missing_revenue_observation_is_allowed(tmp_path):
    file_path = tmp_path / "income_statement.csv"

    df = pd.DataFrame(
        {
            "2025-12-31": [1000.0],
            "2024-12-31": [float("nan")],
        },
        index=["Total Revenue"],
    )

    df.to_csv(file_path)

    validator = FinancialValidator()

    assert validator.validate_file(
        str(file_path),
        "income_statement",
    )


def test_unsupported_statement_fails(tmp_path):
    file_path = tmp_path / "unknown.csv"

    pd.DataFrame(
        {"2025-12-31": [100]},
        index=["Some Metric"],
    ).to_csv(file_path)

    validator = FinancialValidator()

    assert not validator.validate_file(
        str(file_path),
        "unknown_statement",
    )