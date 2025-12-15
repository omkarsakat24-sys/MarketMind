import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import feedparser
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="MarketMind", page_icon="🧠", layout="wide")

# Custom CSS
st.markdown(
    """
<style>
    .stApp { background-color: #0e1117; color: #FAFAFA; }
    h1, h2, h3 { color: #00e676; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #00e676; }
</style>
""",
    unsafe_allow_html=True,
)


# --- 1. HELPER FUNCTIONS (THE BRAIN) ---
# --- HELPER FUNCTIONS ---
def fix_ticker(symbol):
    s = symbol.strip().upper()

    # 1. Map Common Names to Real Tickers
    name_map = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "SENSEX": "^BSESN",
        "FINNIFTY": "^CNXFIN",
        # COMMON STOCKS MAPPING
        "VEDANTA": "VEDL",
        "HDFC": "HDFCBANK",
        "BAJFIN": "BAJFINANCE",
        "M&M": "M&M",
        "MAHINDRA": "M&M",
        "MARUTI": "MARUTI",
        "TITAN": "TITAN",
        "AIRTEL": "BHARTIARTL",
        "JIO": "JIOFIN",
        "POWERGRID": "POWERGRID",
        "NTPC": "NTPC",
    }

    if s in name_map:
        s = name_map[s]  # Convert Name to Ticker (e.g., VEDANTA -> VEDL)

    # 2. Add Extension if missing
    if s.endswith(".NS") or s.endswith(".BO") or s.startswith("^"):
        return s
    return f"{s}.NS"


def fetch_financial_metrics(tickers):
    """Fetches Fundamental Data with Backup Checks."""
    metrics = []
    for t in tickers:
        try:
            ticker_obj = yf.Ticker(t)
            info = ticker_obj.info

            # 1. SMART GROWTH CHECK (Try Annual -> Quarterly -> Earnings Growth)
            rev_g = info.get("revenueGrowth")
            if rev_g is None:
                rev_g = info.get("quarterlyRevenueGrowth")
            if rev_g is None:
                rev_g = info.get("earningsGrowth")
            if rev_g is None:
                rev_g = 0  # Default if absolutely no data found

            # 2. SMART MARGIN CHECK (Try Net -> Operating -> Gross)
            pm = info.get("profitMargins")
            if pm is None:
                pm = info.get("operatingMargins")
            if pm is None:
                pm = info.get("grossMargins")
            if pm is None:
                pm = 0

            mc = info.get("marketCap", 0)
            name = info.get("shortName", t)

            metrics.append(
                {
                    "Ticker": t.replace(".NS", ""),
                    "Name": name,
                    "Rev Growth (%)": rev_g * 100,
                    "Profit Margin (%)": pm * 100,
                    "Market Cap": mc,
                    "Size": np.log(mc) if mc > 0 else 1,
                }
            )
        except Exception as e:
            pass

    return pd.DataFrame(metrics)


# --- SIDEBAR & INPUTS ---
with st.sidebar:
    st.header("⚙️ F&O Data")
    fii_L = st.number_input("FII Longs", 35000)
    fii_S = st.number_input("FII Shorts", 125000)
    dii_L = st.number_input("DII Longs", 55000)
    dii_S = st.number_input("DII Shorts", 25000)
    cli_L = st.number_input("Client Longs", 300000)
    cli_S = st.number_input("Client Shorts", 150000)
    st.divider()
    pcr = st.number_input("PCR", 0.75)
    vix = st.number_input("VIX", 12.5)

# --- MAIN APP ---
st.title("🧠 MarketMind: The Irrationality Scanner")
tabs = st.tabs(
    [
        "🔥 Trap Detector",
        "🧭 Sector Compass",
        "💎 Stage 2",
        "🚀 Hype Meter",
        "📰 News",
        "📐 Gann",
        "🗺️ Heatmap",
        "🧬 Lifecycle",
    ]
)

# TAB 1: TRAP DETECTOR
with tabs[0]:
    tf = fii_L + fii_S
    tc = cli_L + cli_S
    if tf > 0 and tc > 0:
        fp = (fii_L / tf) * 100
        cp = (cli_L / tc) * 100
        dp = (dii_L / (dii_L + dii_S)) * 100 if (dii_L + dii_S) > 0 else 0

        sig, col, msg = "NEUTRAL", "gray", "Market Balanced"
        if cp > 60 and fp < 30:
            sig, col = "BEAR TRAP ⚠️", "red"
            msg = "Retail Buying, FII Selling. Danger."
        elif cp < 40 and fp > 65:
            sig, col = "SMART BUYING 🟢", "green"
            msg = "FII Buying, Retail Scared. Opportunity."
        elif fp < 15:
            sig, col = "ROCKET ALERT 🚀", "orange"
            msg = "Short Covering Rally Likely."

        st.markdown(f"### Signal: :{col}[{sig}]")
        st.info(msg)
        c1, c2 = st.columns(2)
        c1.metric("VIX", vix)
        c2.metric("PCR", pcr)
        st.progress(int(fp), f"FII Bullish: {fp:.1f}%")
        st.progress(int(dp), f"DII Bullish: {dp:.1f}%")
    else:
        st.warning("Enter Data in Sidebar")

# TAB 2: SECTOR COMPASS (Uses get_stock_data)
with tabs[1]:
    if st.button("Scout Sectors"):
        with st.spinner("Analyzing..."):
            secs = {
                "Bank": "^NSEBANK",
                "IT": "^CNXIT",
                "Auto": "^CNXAUTO",
                "Pharma": "^CNXPHARMA",
                "Metal": "^CNXMETAL",
                "FMCG": "^CNXFMCG",
                "Realty": "^CNXREALTY",
            }
            # Here is where it was crashing before. Now get_stock_data is defined above!
            data = get_stock_data(list(secs.values()) + ["^NSEI"], "6mo", "1d")
            res = []
            for n, t in secs.items():
                try:
                    s, i = data[t]["Close"], data["^NSEI"]["Close"]
                    rs = (s / i) * 100
                    ratio = (rs / rs.rolling(20).mean()).iloc[-1] * 100
                    mom = (
                        ratio / ((rs / rs.rolling(20).mean()).shift(10).iloc[-1] * 100)
                    ) * 100
                    q = (
                        "Leading"
                        if ratio > 100 and mom > 100
                        else (
                            "Weakening"
                            if ratio > 100
                            else "Lagging" if ratio < 100 and mom < 100 else "Improving"
                        )
                    )
                    res.append([n, ratio, mom, q])
                except:
                    pass
            df = pd.DataFrame(res, columns=["Sector", "Ratio", "Mom", "Quad"])
            fig = px.scatter(
                df,
                x="Ratio",
                y="Mom",
                color="Quad",
                text="Sector",
                size=[20] * len(df),
                color_discrete_map={
                    "Leading": "#00FF00",
                    "Weakening": "#FFFF00",
                    "Lagging": "#FF0000",
                    "Improving": "#00CCFF",
                },
            )
            fig.update_traces(
                textposition="top center", textfont=dict(size=14, color="white")
            )
            fig.add_hline(100, line_dash="dot")
            fig.add_vline(100, line_dash="dot")
            st.plotly_chart(fig, use_container_width=True)

# TAB 3: STAGE 2
with tabs[2]:
    st.markdown("Enter Stocks (comma separated):")
    u_t = st.text_area("Tickers", "RELIANCE, SBIN, TATAMOTORS, INFY, ITC, TATASTEEL")
    if st.button("Run Scanner"):
        t_l = [fix_ticker(x) for x in u_t.split(",")]
        data = get_stock_data(t_l)
        res = []
        for t in t_l:
            try:
                df = data[t]
                curr = df["Close"].iloc[-1]
                ma = df["Close"].rolling(30).mean().iloc[-1]
                if curr > ma and ma > df["Close"].rolling(30).mean().iloc[-5]:
                    res.append([t, curr, ((curr - ma) / ma) * 100])
            except:
                pass
        st.dataframe(pd.DataFrame(res, columns=["Stock", "Price", "% Above MA"]))

# TAB 4: HYPE METER
with tabs[3]:
    sens = st.slider("Sensitivity", 0.5, 5.0, 1.5, 0.5)
    u_h = st.text_area(
        "Hype Watchlist", "ADANIENT, ZOMATO, SUZLON, IREDA, JIOFIN, RVNL, IDEA, YESBANK"
    )
    if st.button("Scan Hype"):
        h_l = [fix_ticker(x) for x in u_h.split(",")]
        data = get_stock_data(h_l, "1mo", "1d")
        res = []
        for t in h_l:
            try:
                df = data[t]
                if len(df) < 5:
                    continue
                v = (
                    df["Volume"].iloc[-1]
                    if df["Volume"].iloc[-1] > 0
                    else df["Volume"].iloc[-2]
                )
                c = (
                    df["Close"].iloc[-1]
                    if df["Volume"].iloc[-1] > 0
                    else df["Close"].iloc[-2]
                )
                dt = df.index[-1] if df["Volume"].iloc[-1] > 0 else df.index[-2]
                fac = v / df["Volume"].mean()
                if fac > sens:
                    res.append(
                        [t, c, f"{fac:.1f}x", "🔥" if fac > 5 else "⚠️", dt.date()]
                    )
            except:
                pass
        st.dataframe(
            pd.DataFrame(res, columns=["Stock", "Price", "Vol Spike", "Tag", "Date"])
        )

# TAB 5: NEWS
with tabs[4]:
    q = st.text_input("Topic", "Indian Stock Market")
    if st.button("Fetch News"):
        for i in fetch_market_news(q):
            st.markdown(f"**[{i.title}]({i.link})**")

# TAB 6: GANN
with tabs[5]:
    gt = fix_ticker(st.text_input("Ticker", "NIFTY"))
    if st.button("Calculate"):
        d = yf.Ticker(gt).history(period="1y")
        if not d.empty:
            h, l = d["High"].max(), d["Low"].min()
            lev_h, lev_l = calculate_gann_levels(h), calculate_gann_levels(l)
            c1, c2 = st.columns(2)
            c1.metric("Res (360)", f"{lev_h[8]:.2f}")
            c1.metric("Sup (90)", f"{lev_h[2]:.2f}")
            c2.metric("Res (180)", f"{lev_l[7]:.2f}")
            c2.metric("Sup (Base)", f"{lev_l[4]:.2f}")

# TAB 7: HEATMAP
with tabs[6]:
    lists = {
        "Nifty 50": [
            "RELIANCE",
            "TCS",
            "HDFCBANK",
            "ICICIBANK",
            "INFY",
            "BHARTIARTL",
            "ITC",
            "SBIN",
            "LICI",
            "HINDUNILVR",
        ],
        "Bank Nifty": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
    }
    sel = st.selectbox("View:", list(lists.keys()))
    if st.button("Generate Map"):
        ticks = [fix_ticker(x) for x in lists[sel]]
        data = get_stock_data(ticks, "5d", "1d")
        h_data = []
        for t in ticks:
            try:
                df = data[t]
                l_c = df["Close"].iloc[-1]
                p_c = df["Close"].iloc[-2]
                if l_c == 0 or np.isnan(l_c):
                    l_c = df["Close"].iloc[-2]
                    p_c = df["Close"].iloc[-3]
                pct = ((l_c - p_c) / p_c) * 100
                h_data.append(
                    {
                        "Ticker": t.replace(".NS", ""),
                        "Change": pct,
                        "Price": l_c,
                        "Label": f"{t.replace('.NS','')}\n{pct:.2f}%",
                    }
                )
            except:
                pass
        if h_data:
            fig = px.treemap(
                pd.DataFrame(h_data),
                path=["Ticker"],
                values="Price",
                color="Change",
                color_continuous_scale=["#FF0000", "#121212", "#00FF00"],
                color_continuous_midpoint=0,
            )
            fig.update_traces(
                textinfo="label+text",
                texttemplate="%{label}",
                textposition="middle center",
                textfont=dict(size=14, color="white"),
            )
            st.plotly_chart(fig, use_container_width=True)

# TAB 8: CORPORATE LIFECYCLE (Complete)
with tabs[7]:
    st.subheader("🧬 Corporate Lifecycle Matrix")
    mode = st.radio(
        "Mode:", ["Compare Sector (Group)", "Analyze Individual Stock"], horizontal=True
    )

    if mode == "Compare Sector (Group)":
        lists_lc = {
            "Nifty 50": [
                "RELIANCE",
                "TCS",
                "HDFCBANK",
                "INFY",
                "ITC",
                "SBIN",
                "TATAMOTORS",
                "SUNPHARMA",
                "TITAN",
                "BAJFINANCE",
                "ASIANPAINT",
                "MARUTI",
                "ZOMATO",
                "ADANIENT",
            ],
            "Auto Sector": [
                "TATAMOTORS",
                "M&M",
                "MARUTI",
                "BAJAJ-AUTO",
                "EICHERMOT",
                "TVSMOTOR",
                "HEROMOTOCO",
            ],
            "IT Sector": [
                "TCS",
                "INFY",
                "HCLTECH",
                "WIPRO",
                "TECHM",
                "LTIM",
                "PERSISTENT",
            ],
            "Custom": [],
        }
        sel_list = st.selectbox("Select Group:", list(lists_lc.keys()))
        if sel_list == "Custom":
            custom_txt = st.text_area(
                "Enter Tickers (comma separated):", "ZOMATO, PAYTM, NYKAA, IDEA"
            )
            ticks = [fix_ticker(x) for x in custom_txt.split(",")]
        else:
            ticks = [fix_ticker(x) for x in lists_lc[sel_list]]

        if st.button("Generate Matrix"):
            with st.spinner("Analyzing Financials..."):
                df_life = fetch_financial_metrics(ticks)
                if not df_life.empty:
                    conditions = [
                        (df_life["Rev Growth (%)"] > 15)
                        & (df_life["Profit Margin (%)"] < 5),
                        (df_life["Rev Growth (%)"] > 10)
                        & (df_life["Profit Margin (%)"] > 10),
                        (df_life["Rev Growth (%)"] < 10)
                        & (df_life["Profit Margin (%)"] > 15),
                        (df_life["Rev Growth (%)"] < 5)
                        & (df_life["Profit Margin (%)"] < 5),
                    ]
                    choices = [
                        "🚀 Aggressive Growth",
                        "⭐ Prime Champions",
                        "🏰 Mature Cash Cows",
                        "📉 Laggards",
                    ]
                    df_life["Zone"] = np.select(
                        conditions, choices, default="⚖️ Average"
                    )

                    fig = px.scatter(
                        df_life,
                        x="Profit Margin (%)",
                        y="Rev Growth (%)",
                        size="Size",
                        color="Zone",
                        text="Ticker",
                        color_discrete_map={
                            "🚀 Aggressive Growth": "#00CCFF",
                            "⭐ Prime Champions": "#00FF00",
                            "🏰 Mature Cash Cows": "#FFD700",
                            "📉 Laggards": "#FF0000",
                            "⚖️ Average": "#808080",
                        },
                    )
                    fig.add_hline(y=10, line_dash="dot", line_color="gray")
                    fig.add_vline(x=10, line_dash="dot", line_color="gray")
                    fig.update_traces(
                        textposition="top center", textfont=dict(size=13, color="white")
                    )
                    fig.update_layout(
                        plot_bgcolor="#0e1117",
                        paper_bgcolor="#0e1117",
                        font=dict(color="#FAFAFA"),
                        height=600,
                    )
                    st.plotly_chart(fig, use_container_width=True)

    else:  # INDIVIDUAL STOCK MODE
        st.markdown("### 🕵️ Single Stock Deep Dive")
        single_ticker = st.text_input("Enter Stock Name:", "ZOMATO")
        if st.button("Analyze Stock Identity"):
            t = fix_ticker(single_ticker)
            with st.spinner(f"X-Raying {t}..."):
                df_single = fetch_financial_metrics([t])
                if not df_single.empty:
                    row = df_single.iloc[0]
                    rg = row["Rev Growth (%)"]
                    pm = row["Profit Margin (%)"]

                    zone = "⚖️ Average"
                    desc = "Standard performance."
                    color = "gray"
                    if rg > 15 and pm < 5:
                        zone = "🚀 Aggressive Growth (Disruptor)"
                        desc = "High Growth, Low Profit. Betting on Future."
                        color = "blue"
                    elif rg > 10 and pm > 10:
                        zone = "⭐ Prime Champion (Star)"
                        desc = "The Holy Grail. Growing fast AND profitable."
                        color = "green"
                    elif rg < 10 and pm > 15:
                        zone = "🏰 Mature Cash Cow (Stable)"
                        desc = "Slow growth but huge profits. Dividend Payer."
                        color = "orange"
                    elif rg < 5 and pm < 5:
                        zone = "📉 Laggard (Danger)"
                        desc = "Declining growth and low margins. Avoid."
                        color = "red"

                    st.divider()
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("Revenue Growth", f"{rg:.2f}%")
                        st.metric("Profit Margin", f"{pm:.2f}%")
                    with c2:
                        st.markdown(f"## :{color}[{zone}]")
                        st.info(f"**Verdict:** {desc}")
                else:
                    st.error("Could not fetch data.")
