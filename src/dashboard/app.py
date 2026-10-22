import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="FinSight AI Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- HELPER FUNCTIONS -------------------------------------------------------
def fetch_api_data(endpoint: str, symbol: str, params: dict | None = None):
    """Perform a GET request to the FastAPI backend.

    Returns a tuple of (data, error). ``data`` is whatever JSON was returned
    (or ``None`` on failure) and ``error`` is a string describing any problem.
    """
    try:
        url = f"http://127.0.0.1:8000/{endpoint}/{symbol}"
        if params:
            query = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{query}"
        response = requests.get(url, timeout=10)
        payload = response.json()
        if isinstance(payload, dict) and "error" in payload:
            return None, payload["error"]
        return payload, None
    except Exception as exc:
        return None, str(exc)

def format_usd(value):
    """Format a numeric value as US dollars, handling NaN gracefully."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"

def safe_percent(value):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"

# 2. SIDEBAR ---------------------------------------------------------------
st.sidebar.title("⚙️ Control Panel")

# Ticker selection – the reference design only supports US tickers.
TICKER_OPTIONS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"]
selected_ticker = st.sidebar.selectbox("Select Company Ticker", options=TICKER_OPTIONS)

# DCF assumptions – expose sliders that will be sent to the ``intrinsic`` endpoint.
st.sidebar.subheader("DCF Assumptions")
_growth = st.sidebar.slider("Growth Rate (%)", 0, 30, 10) / 100
_discount = st.sidebar.slider("Discount Rate (%)", 5, 20, 12) / 100
_terminal = st.sidebar.slider("Terminal Growth (%)", 0, 5, 3) / 100

# 3. MAIN UI ---------------------------------------------------------------
st.title(f"🔍 Analysis Report – {selected_ticker}")

if selected_ticker:
    # Fetch all required data in parallel (still sequential but concise).
    metrics, m_err = fetch_api_data("metrics", selected_ticker)
    risks, r_err = fetch_api_data("risks", selected_ticker)
    valuation, v_err = fetch_api_data("valuation", selected_ticker)
    intrinsic, i_err = fetch_api_data(
        "intrinsic", selected_ticker, params={"growth": _growth, "discount": _discount, "terminal_growth": _terminal}
    )

    # Consolidate errors.
    errors = [e for e in (m_err, r_err, v_err, i_err) if e]
    if errors:
        st.error("⚠️ API Error: " + "; ".join(errors))

    # ---------------------------------------------------------------------
    # SECTION A – KPI CARDS
    # ---------------------------------------------------------------------
    st.subheader("📌 Key Financials")
    col_rev, col_net, col_pe, col_intr = st.columns(4)
    # Total Revenue
    rev = metrics.get("Total Revenue", {}) if metrics else {}
    col_rev.metric(
        "Total Revenue",
        format_usd(rev.get("current_value")),
        safe_percent(rev.get("yoy_growth")),
    )
    # Net Income
    ni = metrics.get("Net Income", {}) if metrics else {}
    col_net.metric(
        "Net Income",
        format_usd(ni.get("current_value")),
        safe_percent(ni.get("yoy_growth")),
    )
    # P/E Ratio – from valuation endpoint
    pe = valuation.get("P/E_Ratio") if valuation else None
    col_pe.metric("P/E Ratio", f"{pe:.2f}" if isinstance(pe, (int, float)) else "N/A")
    # Intrinsic Value (with valuation status)
    intrinsic_val = intrinsic.get("intrinsic_value") if intrinsic else None
    intrinsic_display = format_usd(intrinsic_val) if intrinsic_val is not None else "N/A"
    current_price = valuation.get("current_price") if valuation else None
    if current_price is None:
        status = "⚠️ Price N/A"
    elif intrinsic_val is None:
        status = "⚠️ Intrinsic N/A"
    else:
        status = "🟢 Undervalued" if intrinsic_val > current_price else "🔴 Overvalued"
    col_intr.metric("Intrinsic Value", intrinsic_display, status)

    # ---------------------------------------------------------------------
    # SECTION B – TIME‑SERIES CHARTS (Revenue & Net Income)
    # ---------------------------------------------------------------------
    st.subheader("📈 Historical Performance")
    # Fetch series for revenue and net income (if available)
    def fetch_series(metric_name):
        data, err = fetch_api_data("timeseries", selected_ticker, params={"metric": metric_name})
        if err or not data:
            return None
        # Expect a list of {"date": "YYYY-MM-DD", "value": number}
        df = pd.DataFrame(data)
        if df.empty:
            return None
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date")
        return df

    rev_series = fetch_series("Total Revenue")
    ni_series = fetch_series("Net Income")

    chart_col1, chart_col2 = st.columns(2)
    if rev_series is not None:
        fig_rev = px.line(rev_series, x="date", y="value", title="Total Revenue Over Time")
        chart_col1.plotly_chart(fig_rev, use_container_width=True)
    else:
        chart_col1.info("Revenue series unavailable")

    if ni_series is not None:
        fig_ni = px.line(ni_series, x="date", y="value", title="Net Income Over Time")
        chart_col2.plotly_chart(fig_ni, use_container_width=True)
    else:
        chart_col2.info("Net Income series unavailable")

    # ---------------------------------------------------------------------
    # SECTION C – RISK AUDIT
    # ---------------------------------------------------------------------
    st.subheader("🚩 Risk Audit")
    if risks:
        for rule, outcome in risks.items():
            message = outcome.get("message", "")
            if outcome.get("triggered"):
                st.error(f"**{rule}**: {message}")
            else:
                st.success(f"**{rule}**: {message}")
    else:
        st.info("No risk data available")

    # ---------------------------------------------------------------------
    # SECTION D – VALUATION SUMMARY & DCF SCENARIOS
    # ---------------------------------------------------------------------
    st.subheader("📊 Valuation Summary")
    val_col1, val_col2 = st.columns(2)
    with val_col1:
        st.write("**Relative Valuation**")
        st.write(f"P/B Ratio: {valuation.get('P/B_Ratio', 'N/A')}" if valuation else "P/B Ratio: N/A")
        st.write(f"Current Price: {format_usd(valuation.get('current_price'))}" if valuation else "Current Price: N/A")
    with val_col2:
        st.write("**DCF Assumptions**")
        st.write(f"Growth Rate: {_growth * 100:.1f}%")
        st.write(f"Discount Rate: {_discount * 100:.1f}%")
        st.write(f"Terminal Growth: {_terminal * 100:.1f}%")

    # DCF Scenario Tabs – placeholder values (actual calculations live in the API)
    if intrinsic:
        st.subheader("🧮 DCF Scenarios")
        scenario_tabs = st.tabs(["Base", "Bull", "Bear"])
        scenario_labels = ["base", "bull", "bear"]
        for tab, label in zip(scenario_tabs, scenario_labels):
            with tab:
                # The API could expose separate endpoints for each scenario; for now we reuse the same value.
                scenario_val = intrinsic.get(f"intrinsic_value_{label}", intrinsic_val)
                st.metric("Intrinsic Value", format_usd(scenario_val))
    else:
        st.info("Intrinsic valuation data unavailable")
else:
    st.info("Select a ticker from the sidebar to begin analysis.")
