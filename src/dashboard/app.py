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
            # This adds ?growth=0.1&discount=0.12 to the URL
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"

        response = requests.get(url)
        data = response.json()

        if "error" in data:
            return None, data["error"]
        return data, None
    except Exception as e:
        return None, str(e)


def format_crores(value):
    """Converts raw numbers to readable Crores."""
    if value is None or pd.isna(value): return "N/A"
    return f"₹{value / 10_000_000:,.2f} Cr"


# --- UI LAYOUT ---

# SIDEBAR: Control Panel
st.sidebar.title("⚙️ Control Panel")

# Define supported tickers without extensions
TICKER_OPTIONS = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "TATAMOTORS"]
selected_ticker = st.sidebar.selectbox("Select Company Ticker", options=TICKER_OPTIONS)

# Append .NS for the backend API calls
symbol = f"{selected_ticker}.NS"

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

    # DCF call with custom assumptions from sidebar
    dcf_params = {"growth": growth_rate, "discount": discount_rate, "terminal_growth": term_growth}
    intrinsic, i_err = fetch_api_data("intrinsic", symbol, params=dcf_params)

    # Error Handling
    if m_err or r_err or v_err or i_err:
        st.error(f"⚠️ API Error: {m_err or r_err or v_err or i_err}")
    else:
        # --- SECTION 1: KPI CARDS ---
        st.subheader("📌 Key Financials")
        col1, col2, col3, col4 = st.columns(4)

        # Revenue KPI
        rev = metrics.get('Total Revenue', {})
        col1.metric("Total Revenue", format_crores(rev.get('current_value')), f"{rev.get('yoy_growth', 0):.2f}%")

        # Net Income KPI
        ni = metrics.get('Net Income', {})
        col2.metric("Net Profit", format_crores(ni.get('current_value')), f"{ni.get('yoy_growth', 0):.2f}%")

        # P/E Ratio
        col3.metric("P/E Ratio", f"{valuation.get('P/E_Ratio', 'N/A'):.2f}")

        # Intrinsic Value
        intrinsic_val = intrinsic.get('intrinsic_value', 0)
        current_price = valuation.get('current_price')

        if current_price is None:
            st.warning("Current price unavailable")
            status = "⚠️ Price N/A"
        else:
            status = "🟢 Undervalued" if intrinsic_val > current_price else "🔴 Overvalued"
        col4.metric("Intrinsic Value", f"₹{intrinsic_val:,.2f}", status)

        # --- SECTION 2: RISK AUDIT ---
        st.markdown("---")
        st.subheader("🚩 Risk Audit")

        # Display risks as a list of alerts
        for rule, result in risks.items():
            if result['triggered']:
                st.error(f"**{rule}**: {result['message']}")
            else:
                st.success(f"**{rule}**: {result['message']}")

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
    st.info("Please enter a company symbol in the sidebar to begin.")
