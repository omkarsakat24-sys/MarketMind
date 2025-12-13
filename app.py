import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="MarketMind", page_icon="🧠", layout="wide")

# Custom CSS for "Bloomberg Dark" Theme
st.markdown(
    """
<style>
    .stApp {
        background-color: #0e1117;
        color: #FAFAFA;
    }
    .metric-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2e3346;
    }
    h1, h2, h3 {
        color: #00e676; /* Neon Green */
        font-family: 'Segoe UI', sans-serif;
    }
    .stAlert {
        background-color: #1e2130;
        color: #ff4b4b;
        border: 1px solid #ff4b4b;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- MODULE 1: TRAP DETECTOR LOGIC ---
def analyze_trap(fii_long, fii_short, client_long, client_short, pcr, vix):
    """
    Analyzes Market Sentiment based on FII vs Client positioning.
    """
    total_fii = fii_long + fii_short
    total_client = client_long + client_short

    # Avoid division by zero
    if total_fii == 0 or total_client == 0:
        return "WAITING FOR DATA", "neutral", "Input Data on Sidebar"

    fii_long_pct = (fii_long / total_fii) * 100
    client_long_pct = (client_long / total_client) * 100

    signal = "NEUTRAL"
    color = "gray"
    msg = "Market is balanced. Follow price action."

    # LOGIC 1: BEAR TRAP (Retail Bullish, FII Bearish)
    if fii_long_pct < 30 and client_long_pct > 60:
        signal = "BEAR TRAP ⚠️"
        color = "red"
        msg = f"Retail is LONG ({client_long_pct:.0f}%), Smart Money is SHORT ({100-fii_long_pct:.0f}%). High risk of crash."
        if pcr > 1.3:
            msg += " PCR is Overbought."

    # LOGIC 2: BULL TRAP (Retail Bearish, FII Bullish)
    elif fii_long_pct > 65 and client_long_pct < 40:
        signal = "SMART BUYING 🟢"
        color = "green"
        msg = "FIIs are aggressively Long. Retail is scared. Buy on dips."

    # LOGIC 3: SHORT COVERING (FIIs exhausted)
    elif fii_long_pct < 15:
        signal = "ROCKET ALERT 🚀"
        color = "orange"
        msg = (
            "FII Shorts are maxed out. Any positive news will trigger a vertical rally."
        )

    return signal, color, msg, fii_long_pct


# --- MODULE 2 & 3: FETCH DATA FUNCTION ---
@st.cache_data(ttl=3600)  # Cache data for 1 hour to speed up app
def get_stock_data(tickers, period="2y", interval="1wk"):
    data = yf.download(
        tickers, period=period, interval=interval, group_by="ticker", progress=False
    )
    return data


# --- MAIN APP LAYOUT ---

# 1. SIDEBAR (The Control Panel)
with st.sidebar:
    st.header("⚙️ Data Input")
    st.markdown("Enter yesterday's F&O data (from Sensibull/NSE):")

    # User Inputs for Trap Detector
    fii_long_qty = st.number_input("FII Index Longs", value=35000)
    fii_short_qty = st.number_input("FII Index Shorts", value=125000)
    client_long_qty = st.number_input("Client Index Longs", value=300000)
    client_short_qty = st.number_input("Client Index Shorts", value=150000)

    input_pcr = st.number_input("Nifty PCR", value=0.75)
    input_vix = st.number_input("India VIX", value=12.5)

    st.markdown("---")
    st.caption("MarketMind v1.0 • Built with Python")

# 2. HEADER
st.title("🧠 MarketMind: The Irrationality Scanner")
st.markdown("Don't trade the Price. Trade the **Behavior**.")

# 3. DASHBOARD TABS
tab1, tab2, tab3, tab4 = st.tabs(
    ["🔥 Trap Detector", "🧭 Sector Compass", "💎 Stage 2 Scanner", "🚀 Hype Meter"]
)


# --- TAB 1: TRAP DETECTOR ---
with tab1:
    signal, color_code, message, fii_pct = analyze_trap(
        fii_long_qty,
        fii_short_qty,
        client_long_qty,
        client_short_qty,
        input_pcr,
        input_vix,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"### Signal: <span style='color:{color_code}'>{signal}</span>",
            unsafe_allow_html=True,
        )
        st.metric("FII Long Exposure", f"{fii_pct:.1f}%", delta_color="normal")

    with col2:
        st.metric("Fear Gauge (VIX)", f"{input_vix}", delta=None)

    with col3:
        st.metric("Greed Gauge (PCR)", f"{input_pcr}", delta=None)

    st.info(f"**Insight:** {message}")

    # Visual Gauge (Simple Progress Bar for now)
    st.write("### FII Sentiment Meter")
    st.progress(int(fii_pct))
    st.caption("0% = Max Bearish | 100% = Max Bullish")

# --- TAB 2: SECTOR COMPASS (UPGRADED VISUALS) ---
with tab2:
    st.subheader("Where is the Money Flowing?")
    st.markdown(
        "Identifying sectors moving from **Lagging (Red)** to **Improving (Blue)**."
    )

    if st.button("Scout Sectors"):
        with st.spinner("Analyzing Sector Rotation..."):
            # Define Major Sectors
            sectors = {
                "Nifty Bank": "^NSEBANK",
                "Nifty IT": "^CNXIT",
                "Nifty Auto": "^CNXAUTO",
                "Nifty Pharma": "^CNXPHARMA",
                "Nifty Metal": "^CNXMETAL",
                "Nifty FMCG": "^CNXFMCG",
                "Nifty Energy": "^CNXENERGY",
                "Nifty Realty": "^CNXREALTY",
                "Nifty PSU Bank": "^CNXPSUBANK",
            }

            # Fetch Data (Optimized)
            sector_data = get_stock_data(
                list(sectors.values()) + ["^NSEI"], period="6mo", interval="1d"
            )
            rrg_results = []

            for name, ticker in sectors.items():
                try:
                    sec_close = sector_data[ticker]["Close"]
                    nifty_close = sector_data["^NSEI"]["Close"]

                    # RRG Math
                    rs_raw = (sec_close / nifty_close) * 100
                    rs_ratio = (rs_raw / rs_raw.rolling(window=20).mean()) * 100
                    rs_mom = (rs_ratio / rs_ratio.shift(10)) * 100

                    curr_ratio = rs_ratio.iloc[-1]
                    curr_mom = rs_mom.iloc[-1]

                    # Determine Quadrant
                    if curr_ratio > 100 and curr_mom > 100:
                        quadrant, color = "Leading", "green"
                    elif curr_ratio > 100 and curr_mom < 100:
                        quadrant, color = "Weakening", "yellow"
                    elif curr_ratio < 100 and curr_mom < 100:
                        quadrant, color = "Lagging", "red"
                    elif curr_ratio < 100 and curr_mom > 100:
                        quadrant, color = "Improving", "blue"

                    rrg_results.append([name, curr_ratio, curr_mom, quadrant, color])

                except Exception:
                    pass

            # Create DataFrame
            df_rrg = pd.DataFrame(
                rrg_results,
                columns=["Sector", "Ratio", "Momentum", "Quadrant", "Color"],
            )

            # --- UPGRADED PLOTLY CHART ---
            fig = px.scatter(
                df_rrg,
                x="Ratio",
                y="Momentum",
                color="Quadrant",
                hover_name="Sector",
                text="Sector",
                title="Sector Rotation Map",
                width=900,
                height=700,
                color_discrete_map={
                    "Leading": "#00FF00",
                    "Weakening": "#FFFF00",
                    "Lagging": "#FF0000",
                    "Improving": "#00CCFF",
                },
                size=[15] * len(df_rrg),
            )  # Make dots bigger

            # Fix Text Position (Smart Labels)
            fig.update_traces(textposition="top center", textfont_size=12)

            # Add Quadrant Backgrounds (The "Crosshair")
            fig.add_shape(
                type="line",
                x0=100,
                y0=df_rrg["Momentum"].min() - 1,
                x1=100,
                y1=df_rrg["Momentum"].max() + 1,
                line=dict(color="gray", dash="dot"),
            )
            fig.add_shape(
                type="line",
                x0=df_rrg["Ratio"].min() - 1,
                y0=100,
                x1=df_rrg["Ratio"].max() + 1,
                y1=100,
                line=dict(color="gray", dash="dot"),
            )

            # Dark Mode & Grid Styling
            fig.update_layout(
                plot_bgcolor="#0e1117",
                paper_bgcolor="#0e1117",
                font=dict(color="#FAFAFA"),
                xaxis=dict(title="Relative Strength (Ratio)", gridcolor="#2e3346"),
                yaxis=dict(title="Momentum (Speed)", gridcolor="#2e3346"),
                showlegend=True,
            )

            st.plotly_chart(fig, use_container_width=True)

            # Highlight Opportunity
            improving = df_rrg[df_rrg["Quadrant"] == "Improving"]
            if not improving.empty:
                st.info(f"💎 **Watchlist:** {', '.join(improving['Sector'].tolist())}")
# --- TAB 3: STAGE 2 SCANNER (Weinstein) ---
with tab3:
    st.subheader("The Stage 2 Hit List")
    st.markdown("Scanning for stocks waking up from slumber (Weekly Chart Breakouts).")

    # Input for tickers (comma separated)
    user_tickers = st.text_area(
        "Enter Stock Tickers (comma separated, add .NS for NSE):",
        "RELIANCE.NS, TATASTEEL.NS, INFY.NS, HDFCBANK.NS, TATAMOTORS.NS, SBIN.NS, ITC.NS, SUNPHARMA.NS",
    )

    if st.button("Run Scanner"):
        ticker_list = [x.strip() for x in user_tickers.split(",")]

        with st.spinner("Checking 30-Week Moving Averages..."):
            data = get_stock_data(ticker_list, period="2y", interval="1wk")

            valid_breakouts = []

            for ticker in ticker_list:
                try:
                    df = data[ticker].copy()

                    # Weinstein Logic
                    df["30W_MA"] = df["Close"].rolling(window=30).mean()

                    current_price = df["Close"].iloc[-1]
                    ma_value = df["30W_MA"].iloc[-1]
                    prev_ma_value = df["30W_MA"].iloc[-5]  # 5 weeks ago

                    # Conditions
                    cond1 = current_price > ma_value  # Price above MA
                    cond2 = ma_value > prev_ma_value  # MA is Rising (Smiling)

                    if cond1 and cond2:
                        dist_from_ma = ((current_price - ma_value) / ma_value) * 100
                        valid_breakouts.append([ticker, current_price, dist_from_ma])

                except Exception as e:
                    continue

            if valid_breakouts:
                st.balloons()
                results_df = pd.DataFrame(
                    valid_breakouts, columns=["Stock", "Price", "% Above MA"]
                )
                st.dataframe(results_df)
                st.markdown("### 📝 Analysis")
                for item in valid_breakouts:
                    st.write(
                        f"✅ **{item[0]}** is in a confirmed Uptrend (Stage 2). The 30-Week MA is smiling."
                    )
            else:
                st.warning("No Stage 2 Breakouts found in this list.")
# --- TAB 4: HYPE METER (Volume Shockers) ---
# Add this code at the end of your app.py, inside the 'with tab4:' block (create the tab first)

# IMPORTANT: Scroll up to line 95 where you defined 'tab1, tab2, tab3'
# and CHANGE it to: tab1, tab2, tab3, tab4 = st.tabs(["🔥 Trap Detector", "🧭 Sector Compass", "💎 Stage 2 Scanner", "🚀 Hype Meter"])

with tab4:
    st.subheader("The Hype Meter: Retail Euphoria Tracker")
    st.markdown(
        "Scanning for stocks with **Abnormal Volume** (>500% of average). This indicates extreme retail herding or insider activity."
    )

    # A list of popular High-Beta / Retail favorite stocks to scan
    # You can add more .NS tickers here
    hype_tickers = st.text_area(
        "Watchlist (High Beta / Small Caps):",
        "SUZLON.NS, IDEA.NS, YESBANK.NS, ZOMATO.NS, PAYTM.NS, IEX.NS, DELTACORP.NS, RPOWER.NS, JPPOWER.NS, TRIDENT.NS, URJA.NS",
    )

    if st.button("Scan for Hype"):
        hype_list = [x.strip() for x in hype_tickers.split(",")]

        with st.spinner("Measuring Crowd Madness..."):
            # Fetch data for last 1 month to calculate average volume
            data = get_stock_data(hype_list, period="1mo", interval="1d")

            hype_results = []

            for ticker in hype_list:
                try:
                    df = data[ticker].copy()

                    # Get yesterday's volume and the 20-day average volume
                    last_vol = df["Volume"].iloc[-1]
                    avg_vol = df["Volume"].mean()

                    # Calculate the "Hype Factor" (Current Vol / Avg Vol)
                    hype_factor = last_vol / avg_vol

                    # Price Change
                    last_close = df["Close"].iloc[-1]
                    prev_close = df["Close"].iloc[-2]
                    pct_change = ((last_close - prev_close) / prev_close) * 100

                    # Filter: Only show if Volume is > 3x (300%) normal
                    if hype_factor > 3:
                        status = "🔥 EXTREME" if hype_factor > 5 else "⚠️ HIGH"
                        hype_results.append(
                            [
                                ticker,
                                last_close,
                                f"{pct_change:.2f}%",
                                f"{hype_factor:.1f}x",
                                status,
                            ]
                        )

                except Exception as e:
                    continue

            if hype_results:
                st.markdown("### 🚨 Abnormal Activity Detected")
                df_hype = pd.DataFrame(
                    hype_results,
                    columns=[
                        "Stock",
                        "Price",
                        "Change %",
                        "Volume Spike (x)",
                        "Intensity",
                    ],
                )
                st.dataframe(df_hype)

                # Insight Generation
                for row in hype_results:
                    if "EXTREME" in row[4]:
                        st.error(
                            f"**{row[0]}** is seeing {row[3]} times normal volume! This is a massive Retail/Operator pump. Be careful."
                        )
            else:
                st.success(
                    "Market is calm. No abnormal volume spikes detected in this list."
                )
