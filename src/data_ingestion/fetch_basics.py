import yfinance as yf
import os
import pandas as pd

# --- CONFIGURATION ---
# We define the base path once. This prevents "Path Fragility".
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

def get_ticker_path(ticker_symbol):
    """Returns the absolute path to a ticker's raw data folder."""
    folder_path = os.path.join(RAW_DATA_DIR, ticker_symbol)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def fetch_and_save(ticker_obj, attribute_name, ticker_symbol):
    """
    Helper to handle the Bronze Layer logic:
    Check Disk -> If missing, Fetch from API -> Save to Disk.
    """
    file_path = os.path.join(get_ticker_path(ticker_symbol), f"{attribute_name}.csv")

    if os.path.exists(file_path):
        # index_col=0 ensures the date/index is restored correctly
        return pd.read_csv(file_path, index_col=0)

    # Fetch from API
    data = getattr(ticker_obj, attribute_name)
    # index=True is used because financial data indices (dates) are critical
    data.to_csv(file_path, index=True)
    return data

def get_financial_info(ticker_list):
    financials = {}
    for tick in ticker_list:
        try:
            # We only create the Ticker object once per company
            ticker_obj = yf.Ticker(tick)

            company_info = {
                "income_statement": fetch_and_save(ticker_obj, "financials", tick),
                "cashflow": fetch_and_save(ticker_obj, "cashflow", tick),
                "balance_sheet": fetch_and_save(ticker_obj, "balance_sheet", tick),
            }
            financials[tick] = company_info
            print(f"Successfully processed {tick}")

        except Exception as e:
            print(f"Critical error processing {tick}: {e}")
            continue

    return financials

if __name__ == "__main__":
    ticker_list = ["TCS.NS", "RELIANCE.NS", "INFY.NS",
                   "HDFCBANK.NS", "ICICIBANK.NS"]

    # This now handles both saving and loading automatically (Caching)
    financials = get_financial_info(ticker_list)

    if "TCS.NS" in financials:
        print("\n--- TCS Income Statement (First 5 rows) ---")
        print(financials["TCS.NS"]["income_statement"].head())
    else:
        print("TCS data not found.")
