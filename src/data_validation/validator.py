import pandas as pd
import os
import sys

# This allows the script to find the 'src' package even if run as a script
# though the professional way is to run with 'python -m src.data_validation.validator'
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".."))

try:
    from src.data_ingestion.fetch_basics import get_financial_info
except ImportError:
    # Fallback for different execution environments
    from ..data_ingestion.fetch_basics import get_financial_info

def validate_financials(ticker, df):
    """

    Performs sanity checks on a financial DataFrame.
    Returns a list of warnings.
    """
    warnings = []

    # 1. NaN Check: .isnull().values.any() returns a single True/False
    if df.isnull().values.any():
        warnings.append(f"[{ticker}] Missing values (NaN) detected")

    # 2. Revenue Check: Use .loc to access the row
    if "Total Revenue" in df.index:
        revenue_row = df.loc["Total Revenue"]
        # Check if any value in the row is negative
        if (revenue_row < 0).any():
            warnings.append(f"[{ticker}] Negative revenue detected")

    return warnings

if __name__ == "__main__":
    ticker_list = ["TCS.NS", "RELIANCE.NS", "INFY.NS",
                   "HDFCBANK.NS", "ICICIBANK.NS"]

    print("Fetching data for validation...")
    financials = get_financial_info(ticker_list)

    all_warnings = []

    for tick in ticker_list:
        if tick in financials:
            # financials[tick] is a dict: {"income_statement": df, ...}
            # We iterate over the .values() to get the actual DataFrames
            for df in financials[tick].values():
                all_warnings.extend(validate_financials(tick, df))

    if all_warnings:
        print("\n⚠️ Validation Warnings Found:")
        for w in all_warnings:
            print(w)
    else:
        print("\n✅ All data passed sanity checks!")
