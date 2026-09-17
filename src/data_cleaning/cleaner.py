import pandas as pd
import os

# --- CONFIGURATION ---
# Maintaining consistency with the project's path management
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SILVER_DATA_DIR = os.path.join(BASE_DIR, "data", "silver")

def clean_financial_df(df, ticker, file_name):
    """
    Silver Layer Processing:
    Transforms raw Bronze data into cleaned, standardized data.
    """
    print(f"Cleaning {file_name} for {ticker}...")

    # 1. Copy the dataframe to avoid modifying the original (Immutability)
    cleaned_df = df.copy()

    # 2. Handle Missing Values (Imputation)
    # In finance, a NaN often means the value is effectively 0.
    # We use fillna(0) to ensure mathematical operations don't crash.
    cleaned_df = cleaned_df.fillna(0)

    # 3. Type Casting (Standardization)
    # We ensure all columns are numeric.
    # errors='coerce' turns unparseable strings into NaN, which we then fill with 0.
    cleaned_df = cleaned_df.apply(lambda col: pd.to_numeric(col, errors='coerce')).fillna(0)

    # 4. The Silver Save
    # We save to a separate directory to keep our 'Bronze' (raw) data untouched.
    ticker_folder = os.path.join(SILVER_DATA_DIR, ticker)
    os.makedirs(ticker_folder, exist_ok=True)

    file_path = os.path.join(ticker_folder, file_name)
    cleaned_df.to_csv(file_path, index=True)

    return cleaned_df

if __name__ == "__main__":

    # Sample: Use TCS balance sheet from Bronze layer
    try:
        # Path to bronze file
        # Note: In a real pipeline, this path would be passed by the orchestrator
        sample_path = os.path.join(BASE_DIR, "data", "raw", "TCS.NS", "balance_sheet.csv")

        if os.path.exists(sample_path):
            raw_df = pd.read_csv(sample_path, index_col=0)
            cleaned_df = clean_financial_df(raw_df, "TCS.NS", "balance_sheet.csv")

            print("\n✅ Cleaning Successful!")
            print("Raw Data Sample (with NaNs potentially):")
            print(raw_df.head(3))
            print("\nCleaned Data Sample (No NaNs, all numeric):")
            print(cleaned_df.head(3))
        else:
            print("Sample bronze file not found. Please run fetch_basics.py first.")

    except Exception as e:
        print(f"Error during cleaning test: {e}")
