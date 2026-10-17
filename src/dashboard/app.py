import streamlit as st
import requests
import pandas as pd

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Fundamental AI Intelligence",
    page_icon="📈",
    layout="wide"
)


# --- HELPER FUNCTIONS ---
def fetch_api_data(endpoint, symbol, params=None):
    """Generic function to handle all API calls and errors."""
    try:
        url = f"http://127.0.0.1:8000/{endpoint}/{symbol}"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"
        response = requests.get(url)
        data = response.json()
        if "error" in data:
            return None, data["error"]
        return data, None
    except Exception as e:
        return None, str(e)


def format_usd(value):
    """Format a numeric value as US dollars (no Indian Crores)."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"


# --- UI LAYOUT ---

# SIDEBAR: Control Panel
st.sidebar.title("⚙️ Control Panel")

# Define supported US tickers (you can edit this list as needed)
TICKER_OPTIONS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"]
selected_ticker = st.sidebar.selectbox("Select Company Ticker", options=TICKER_OPTIONS)

# No market suffix is added – the backend expects a plain US ticker.
symbol = selected_ticker

st.sidebar.markdown("---")
st.sidebar.subheader("DCF Assumptions")
growth_rate = st.sidebar.slider("Growth Rate (%)", 0, 30, 10) / 100
discount_rate = st.sidebar.slider("Discount Rate (%)", 5, 20, 12) / 100
term_growth = st.sidebar.slider("Terminal Growth (%)", 0, 5, 3) / 100

# MAIN PAGE
st.title(f"🔍 Analysis Report: {symbol}")

if symbol:
    # 1. FETCH ALL DATA
    metrics, m_err = fetch_api_data("metrics", symbol)
    risks, r_err = fetch_api_data("risks", symbol)
    valuation, v_err = fetch_api_data("valuation", symbol)
    dcf_params = {"growth": growth_rate, "discount": discount_rate, "terminal_growth": term_growth}
    intrinsic, i_err = fetch_api_data("intrinsic", symbol, params=dcf_params)

    metrics = metrics or {}
    risks = risks or {}
    valuation = valuation or {}
    intrinsic = intrinsic or {}

    errors = [e for e in (m_err, r_err, v_err, i_err) if e]
    if errors:
        st.error(f"⚠️ API Error: {'; '.join(errors)}")

    # --- SECTION 1: KPI CARDS ---
    st.subheader("📌 Key Financials")
    col1, col2, col3, col4 = st.columns(4)

    rev = metrics.get('Total Revenue', {})
    col1.metric("Total Revenue", format_usd(rev.get('current_value')),
                 f"{rev.get('yoy_growth', 0):.2f}%")

    ni = metrics.get('Net Income', {})
    col2.metric("Net Profit", format_usd(ni.get('current_value')),
                 f"{ni.get('yoy_growth', 0):.2f}%")

    pe_ratio = valuation.get('P/E_Ratio')
    pe_display = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
    col3.metric("P/E Ratio", pe_display)

    intrinsic_val = intrinsic.get('intrinsic_value')
    intrinsic_display = format_usd(intrinsic_val) if intrinsic_val is not None else "N/A"
    current_price = valuation.get('current_price')
    if current_price is None:
        st.warning("Current price unavailable")
        status = "⚠️ Price N/A"
    elif intrinsic_val is None:
        status = "⚠️ Intrinsic N/A"
    else:
        status = "🟢 Undervalued" if intrinsic_val > current_price else "🔴 Overvalued"
    col4.metric("Intrinsic Value", intrinsic_display, status)

    # --- SECTION 2: RISK AUDIT ---
    st.markdown("---")
    st.subheader("🚩 Risk Audit")
    if risks:
        for rule, result in risks.items():
            if result.get('triggered'):
                st.error(f"**{rule}**: {result.get('message')}")
            else:
                st.success(f"**{rule}**: {result.get('message')}")
    else:
        st.info("No risk data available")

    # --- SECTION 3: VALUATION DETAILS ---
    st.markdown("---")
    st.subheader("📈 Valuation Summary")
    val_col1, val_col2 = st.columns(2)
    with val_col1:
        st.write("**Relative Valuation**")
        st.write(f"P/B Ratio: {valuation.get('P/B_Ratio', 'N/A')}")
    with val_col2:
        st.write("**DCF Assumptions**")
        st.write(f"Growth: {growth_rate * 100}% | Discount: {discount_rate * 100}%")
else:
    st.info("Please select a company ticker in the sidebar to begin.")
