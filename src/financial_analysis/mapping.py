# in the yfinance data each company has data with different
# title or name like one has "Net Income" but other has
# Net Income Common Stockholders

# so this is just a standardize alias system

METRIC_MAP = {
    "net_income": [
        "Net Income",
        "Net Income Common Stockholders",
        "Net Income Continuous Operations"
    ],
    "revenue": [
        "Total Revenue",
        "Operating Revenue",
        "Revenue"
    ],
    "equity": [
        "Stockholders Equity",
        "Total Equity",
        "Common Stock Equity"
    ],
    "total_assets": [
        "Total Assets"
    ],
    "total_debt": [
        "Total Debt",
        "Long Term Debt",
        "Current Debt"
    ],
}