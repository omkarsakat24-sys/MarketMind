import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import feedparser

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


# --- MODULE 1: TRAP DETECTOR LOGIC (NOW WITH DIIs!) ---
def analyze_trap(
    fii_long, fii_short, dii_long, dii_short, client_long, client_short, pcr, vix
):
    total_fii = fii_long + fii_short
    total_dii = dii_long + dii_short
    total_client = client_long + client_short

    if total_fii == 0 or total_client == 0 or total_dii == 0:
        return "WAITING FOR DATA", "gray", "Input Data on Sidebar", 0, 0

    fii_long_pct = (fii_long / total_fii) * 100
    dii_long_pct = (dii_long / total_dii) * 100
    client_long_pct = (client_long / total_client) * 100

    signal = "NEUTRAL"
    color = "gray"
    msg = "Market is balanced. Follow price action."

    # --- THE LOGIC ENGINE ---

    # 1. BEAR TRAP (Retail Bullish, Big Money Bearish)
    if client_long_pct > 60 and fii_long_pct < 30:
        signal = "BEAR TRAP ⚠️"
        color = "red"
        msg = f"Retail is buying ({client_long_pct:.0f}%) while FIIs are shorting ({100-fii_long_pct:.0f}%)."
        if dii_long_pct < 40:
            msg += " Even DIIs are not supporting! CRASH RISK HIGH."
        else:
            msg += " However, DIIs are buying support. Expect choppy range."

    # 2. BULL TRAP (Retail Bearish, Big Money Bullish)
    elif client_long_pct < 40 and fii_long_pct > 65:
        signal = "SMART BUYING 🟢"
        color = "green"
        msg = "FIIs are Long. Retail is scared."
        if dii_long_pct > 60:
            msg += " DIIs are also Long. Double Engine rally possible!"

    # 3. SHORT COVERING (FIIs Exhausted)
    elif fii_long_pct < 15:
        signal = "ROCKET ALERT 🚀"
        color = "orange"
        msg = (
            "FII Shorts are maxed out. Any positive news will trigger a vertical rally."
        )

    return signal, color, msg, fii_long_pct, dii_long_pct


# --- DATA FETCHING FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_stock_data(tickers, period="2y", interval="1wk"):
    data = yf.download(
        tickers, period=period, interval=interval, group_by="ticker", progress=False
    )
    return data


@st.cache_data(ttl=600)
def fetch_market_news(query="Indian Stock Market"):
    if not query:
        return []
    clean_query = query.replace(" ", "%20")
    rss_url = (
        f"https://news.google.com/rss/search?q={clean_query}&hl=en-IN&gl=IN&ceid=IN:en"
    )
    try:
        feed = feedparser.parse(rss_url)
        return feed.entries[:10]
    except Exception:
        return []


# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("⚙️ Data Input")
    st.markdown("Enter yesterday's F&O data:")

    # FII Inputs
    st.subheader("FII (Foreign)")
    fii_long_qty = st.number_input("FII Longs", value=35000)
    fii_short_qty = st.number_input("FII Shorts", value=125000)

    # DII Inputs (NEW!)
    st.subheader("DII (Domestic)")
    dii_long_qty = st.number_input("DII Longs", value=55000)
    dii_short_qty = st.number_input("DII Shorts", value=25000)

    # Client Inputs
    st.subheader("Client (Retail)")
    client_long_qty = st.number_input("Client Longs", value=300000)
    client_short_qty = st.number_input("Client Shorts", value=150000)

    st.divider()
    input_pcr = st.number_input("Nifty PCR", value=0.75)
    input_vix = st.number_input("India VIX", value=12.5)

# --- MAIN DASHBOARD ---
st.title("🧠 MarketMind: The Irrationality Scanner")
st.markdown("Don't trade the Price. Trade the **Behavior**.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "🔥 Trap Detector",
        "🧭 Sector Compass",
        "💎 Stage 2 Scanner",
        "🚀 Hype Meter",
        "📰 Live News",
    ]
)

# --- TAB 1: TRAP DETECTOR (UPGRADED) ---
with tab1:
    signal, color_code, message, fii_pct, dii_pct = analyze_trap(
        fii_long_qty,
        fii_short_qty,
        dii_long_qty,
        dii_short_qty,
        client_long_qty,
        client_short_qty,
        input_pcr,
        input_vix,
    )

    # Top Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"### Signal: <span style='color:{color_code}'>{signal}</span>",
            unsafe_allow_html=True,
        )
    with col2:
        st.metric("Fear Gauge (VIX)", f"{input_vix}")
    with col3:
        st.metric("Greed Gauge (PCR)", f"{input_pcr}")

    st.info(f"**Insight:** {message}")

    # The Battle Meter
    st.write("### ⚔️ The Institutional Battle")

    col_fii, col_dii = st.columns(2)
    with col_fii:
        st.write(f"**FII Sentiment (Foreign)**: {fii_pct:.1f}% Bullish")
        st.progress(int(fii_pct))

    with col_dii:
        st.write(f"**DII Sentiment (Domestic)**: {dii_pct:.1f}% Bullish")
        st.progress(int(dii_pct))

    st.caption(
        "Note: Usually DIIs buy when FIIs sell. If BOTH bars are low (Red), the market has no support."
    )

# --- TAB 2: SECTOR COMPASS ---
with tab2:
    st.subheader("Where is the Money Flowing?")
    if st.button("Scout Sectors"):
        with st.spinner("Analyzing Sector Rotation..."):
            sectors = {
                "Nifty Bank": "^NSEBANK",
                "Nifty IT": "^CNXIT",
                "Nifty Auto": "^CNXAUTO",
                "Nifty Pharma": "^CNXPHARMA",
                "Nifty Metal": "^CNXMETAL",
                "Nifty FMCG": "^CNXFMCG",
                "Nifty Energy": "^CNXENERGY",
                "Nifty Realty": "^CNXREALTY",
            }
            sector_data = get_stock_data(
                list(sectors.values()) + ["^NSEI"], period="6mo", interval="1d"
            )
            rrg_results = []

            for name, ticker in sectors.items():
                try:
                    sec_close = sector_data[ticker]["Close"]
                    nifty_close = sector_data["^NSEI"]["Close"]
                    rs_raw = (sec_close / nifty_close) * 100
                    rs_ratio = (rs_raw / rs_raw.rolling(window=20).mean()) * 100
                    rs_mom = (rs_ratio / rs_ratio.shift(10)) * 100
                    curr_ratio = rs_ratio.iloc[-1]
                    curr_mom = rs_mom.iloc[-1]

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

            df_rrg = pd.DataFrame(
                rrg_results,
                columns=["Sector", "Ratio", "Momentum", "Quadrant", "Color"],
            )
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
            )
            fig.update_traces(textposition="top center", textfont_size=12)
            fig.add_hline(y=100, line_dash="dot", line_color="gray")
            fig.add_vline(x=100, line_dash="dot", line_color="gray")
            fig.update_layout(
                plot_bgcolor="#0e1117",
                paper_bgcolor="#0e1117",
                font=dict(color="#FAFAFA"),
            )
            st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: STAGE 2 SCANNER ---
with tab3:
    st.subheader("The Stage 2 Hit List")
    user_tickers = st.text_area(
        "Enter Stock Tickers (add .NS):",
        "RELIANCE.NS, TATASTEEL.NS, INFY.NS, HDFCBANK.NS, TATAMOTORS.NS, SBIN.NS, ITC.NS",
    )
    if st.button("Run Scanner"):
        ticker_list = [x.strip() for x in user_tickers.split(",")]
        with st.spinner("Checking Weekly Charts..."):
            data = get_stock_data(ticker_list, period="2y", interval="1wk")
            valid_breakouts = []
            for ticker in ticker_list:
                try:
                    df = data[ticker].copy()
                    df["30W_MA"] = df["Close"].rolling(window=30).mean()
                    current_price = df["Close"].iloc[-1]
                    ma_value = df["30W_MA"].iloc[-1]
                    prev_ma_value = df["30W_MA"].iloc[-5]
                    if current_price > ma_value and ma_value > prev_ma_value:
                        dist = ((current_price - ma_value) / ma_value) * 100
                        valid_breakouts.append([ticker, current_price, dist])
                except Exception:
                    continue
            if valid_breakouts:
                st.balloons()
                st.dataframe(
                    pd.DataFrame(
                        valid_breakouts, columns=["Stock", "Price", "% Above MA"]
                    )
                )
            else:
                st.warning("No Stage 2 Breakouts found.")

# --- TAB 4: HYPE METER ---
with tab4:
    st.subheader("The Hype Meter")
    hype_tickers = st.text_area(
        "Watchlist:", "SUZLON.NS, ZOMATO.NS, PAYTM.NS, IEX.NS, TRIDENT.NS"
    )
    if st.button("Scan for Hype"):
        hype_list = [x.strip() for x in hype_tickers.split(",")]
        with st.spinner("Scanning..."):
            data = get_stock_data(hype_list, period="1mo", interval="1d")
            hype_results = []
            for ticker in hype_list:
                try:
                    df = data[ticker].copy()
                    if len(df) < 20:
                        continue
                    hype_factor = df["Volume"].iloc[-1] / df["Volume"].mean()
                    if hype_factor > 3:
                        status = "🔥 EXTREME" if hype_factor > 5 else "⚠️ HIGH"
                        hype_results.append(
                            [
                                ticker,
                                df["Close"].iloc[-1],
                                f"{hype_factor:.1f}x",
                                status,
                            ]
                        )
                except Exception:
                    continue
            if hype_results:
                st.dataframe(
                    pd.DataFrame(
                        hype_results,
                        columns=["Stock", "Price", "Volume Spike", "Intensity"],
                    )
                )
            else:
                st.success("No volume spikes detected.")

# --- TAB 5: LIVE NEWS ---
# --- TAB 5: LIVE NEWS (Search Anything) ---
# --- TAB 5: LIVE NEWS (Search Anything) ---
with tab5:
    st.header("📰 The Market Narrative")
    st.markdown(
        "Context Check: Search for the specific stock you found in the scanner."
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        # UPGRADE: Changed from 'selectbox' to 'text_input' so you can type anything
        # We set a default value to "Indian Stock Market"
        news_topic = st.text_input(
            "Search News (Type Stock Name):", "Indian Stock Market"
        )

    with col2:
        st.write("")
        st.write("")
        if st.button("📢 Fetch News", type="primary", use_container_width=True):
            st.session_state["fetch_news"] = True

    st.divider()

    try:
        if news_topic:
            with st.spinner(f"Searching Google News for '{news_topic}'..."):
                news_items = fetch_market_news(news_topic)

                if not news_items:
                    st.warning(
                        f"No recent news found for '{news_topic}'. Try typing the full company name."
                    )

                for item in news_items:
                    pub_time = (
                        item.published.replace("+0530", "")
                        if hasattr(item, "published")
                        else ""
                    )
                    with st.expander(f"📄 {item.title}"):
                        st.caption(f"🕒 {pub_time}")
                        st.markdown(f"**[Read Full Story]({item.link})**")
    except Exception as e:
        st.error(f"Error fetching news: {e}")
