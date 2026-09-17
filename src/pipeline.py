from src.data_ingestion.fetch_basics import get_financial_info
from src.data_validation.validator import validate_financials
from src.data_cleaning.cleaner import clean_financial_df


def run_pipeline(ticker_list):
    print("🚀 Starting Fundamental Intelligence Pipeline...")
    print("-" * 50)

    # Step 1: Ingestion (Bronze Layer)
    # Fetches data and saves it as Raw CSVs
    all_data=get_financial_info(ticker_list)
    processed_count=0
    for tick in ticker_list:
        if tick not in all_data:
            print(f"❌ Skipping {tick}: No data available.")
            continue
        print(f"\nProcessing {tick}:")
        company_data = all_data[tick]
        for statement_name,data_frame in company_data.items():
            # step 2 validating
            warnings=validate_financials(tick,data_frame)
            if warnings:
                for warning in warnings:
                    print(f"  ⚠️ {warning}")
            else:
                print(f"  ✅ {statement_name} passed validation.")
                # step 3 cleaning :
            clean_financial_df(data_frame, tick,f"{statement_name}.csv" )
            print(f"💾 {statement_name} saved to Silver Layer.")
        processed_count+=1

    print("-" * 50)
    print(f"🏁 Pipeline Complete! Processed {processed_count}/{len(ticker_list)} companies.")
    return processed_count


if __name__ == "__main__":
    TARGET_TICKERS= ["TCS.NS", "RELIANCE.NS", "INFY.NS",
                   "HDFCBANK.NS", "ICICIBANK.NS"]

    # run the orchestrator
    run_pipeline(TARGET_TICKERS)