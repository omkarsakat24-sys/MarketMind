import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import feedparser
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="MarketMind", page_icon="🧠", layout="wide")

# Custom CSS for "Bloomberg Dark" Theme
st.markdown(
    """
<style>
    .stApp { background-color: #0e1117; color: #FAFAFA; }
    h1, h2, h3 { color: #00e676; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    /* Make Metric Values Bigger */
    div[data-testid="stMetricValue"] { font-size: 24px; color: #00e676; }
</style>
""",
    unsafe_allow_html=True,
)


# --- HELPER: SMART TICKER FIXER ---
def fix_ticker(symbol):
    s = symbol.strip().upper()
    index_map = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "NIFTY 50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "BANK NIFTY": "^NSEBANK",
        "SENSEX": "^BSESN",
        "FINNIFTY": "^CNXFIN",
    }
    if s in index_map:
        return index_map[s]
    if s.endswith(".NS") or s.endswith(".BO") or s.startswith("^"):
        return s
    return f"{s}.NS"


# --- LOGIC MODULES ---
def analyze_trap(
    fii_long, fii_short, dii_long, dii_short, client_long, client_short, pcr, vix
):
    total_fii = fii_long + fii_short
    total_dii = dii_long + dii_short
    total_client = client_long + client_short

    if total_fii == 0 or total_client == 0:
        return "WAITING", "gray", "Input Data", 0, 0

    fii_pct = (fii_long / total_fii) * 100
    dii_pct = (dii_long / total_dii) * 100
    client_pct = (client_long / total_client) * 100

    signal, color, msg = "NEUTRAL", "gray", "Market is balanced."

    if client_pct > 60 and fii_pct < 30:
        signal, color = "BEAR TRAP ⚠️", "red"
        msg = f"Retail Long ({client_pct:.0f}%), FII Short ({100-fii_pct:.0f}%). Crash Risk."
    elif client_pct < 40 and fii_pct > 65:
        signal, color = "SMART BUYING 🟢", "green"
        msg = f"FII Long ({fii_pct:.0f}%), Retail Scared. Buy Dips."
    elif fii_pct < 15:
        signal, color = "ROCKET ALERT 🚀", "orange"
        msg = "FII Shorts Maxed Out. Short Covering Rally Imminent."

    return signal, color, msg, fii_pct, dii_pct


@st.cache_data(ttl=600)
def get_stock_data(tickers, period="2y", interval="1wk"):
    return yf.download(
        tickers, period=period, interval=interval, group_by="ticker", progress=False
    )


@st.cache_data(ttl=600)
def fetch_market_news(query="Indian Stock Market"):
    if not query:
        return []
    clean_query = query.replace(" ", "%20")
    rss_url = (
        f"https://news.google.com/rss/search?q={clean_query}&hl=en-IN&gl=IN&ceid=IN:en"
    )
    try:
        return feedparser.parse(rss_url).entries[:10]
    except:
        return []


def calculate_gann_levels(price):
    sq = np.sqrt(price)
    return [
        (sq - 2) ** 2,
        (sq - 1) ** 2,
        (sq - 0.5) ** 2,
        (sq - 0.25) ** 2,
        price,
        (sq + 0.25) ** 2,
        (sq + 0.5) ** 2,
        (sq + 1) ** 2,
        (sq + 2) ** 2,
    ]


# --- SIDEBAR ---
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
        "💎 Stage 2 Scanner",
        "🚀 Hype Meter",
        "📰 Live News",
        "📐 Gann Master",
        "🗺️ Heatmap",
    ]
)

# TAB 1: TRAP DETECTOR
with tabs[0]:
    sig, col, txt, fpKg, dpKg = analyze_trap(
        fii_L, fii_S, dii_L, dii_S, cli_L, cli_S, pcr, vix
    )
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"## {sig}")
    c2.metric("VIX", vix)
    c3.metric("PCR", pcr)
    st.info(txt)
    st.progress(int(fpKg), text=f"FII Bullishness: {fpKg:.1f}%")
    st.progress(int(dpKg), text=f"DII Bullishness: {dpKg:.1f}%")

# TAB 2: SECTOR COMPASS (CRYSTAL CLEAR VERSION)
with tabs[1]:
    st.markdown("### 🧭 Relative Rotation Graph (RRG)")
    if st.button("Scout Sectors"):
        with st.spinner("Analyzing Sector Rotation..."):
            secs = {
                "Bank": "^NSEBANK",
                "IT": "^CNXIT",
                "Auto": "^CNXAUTO",
                "Pharma": "^CNXPHARMA",
                "Metal": "^CNXMETAL",
                "FMCG": "^CNXFMCG",
                "Realty": "^CNXREALTY",
                "Energy": "^CNXENERGY",
            }
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

            # PLOT WITH TEXT LABELS
            fig = px.scatter(
                df,
                x="Ratio",
                y="Mom",
                color="Quad",
                text="Sector",
                size=[20] * len(df),
                title="Where is Money Flowing?",
                color_discrete_map={
                    "Leading": "#00FF00",
                    "Weakening": "#FFFF00",
                    "Lagging": "#FF0000",
                    "Improving": "#00CCFF",
                },
            )

            # Force text to always show
            fig.update_traces(
                textposition="top center", textfont=dict(size=14, color="white")
            )
            fig.add_hline(100, line_dash="dot", line_color="gray")
            fig.add_vline(100, line_dash="dot", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)

            # CRYSTAL CLEAR TABLE
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.success("✅ **LEADING (Buy These):**")
                leaders = df[df["Quad"] == "Leading"]["Sector"].tolist()
                st.write(", ".join(leaders) if leaders else "None")

                st.info("💎 **IMPROVING (Watch These):**")
                improvers = df[df["Quad"] == "Improving"]["Sector"].tolist()
                st.write(", ".join(improvers) if improvers else "None")

            with c2:
                st.error("❌ **LAGGING (Avoid These):**")
                laggers = df[df["Quad"] == "Lagging"]["Sector"].tolist()
                st.write(", ".join(laggers) if laggers else "None")

                st.warning("⚠️ **WEAKENING (Book Profit):**")
                weakeners = df[df["Quad"] == "Weakening"]["Sector"].tolist()
                st.write(", ".join(weakeners) if weakeners else "None")

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

# TAB 6: GANN MASTER (RESTORED BEST LAYOUT)
with tabs[5]:
    st.subheader("📐 Gann Square of 9 Calculator")
    gt = fix_ticker(st.text_input("Enter Ticker (e.g., NIFTY, RELIANCE):", "NIFTY"))

    if st.button("Calculate Levels"):
        d = yf.Ticker(gt).history(period="1y")
        if not d.empty:
            h, l = d["High"].max(), d["Low"].min()
            cur = d["Close"].iloc[-1]
            h_dt = d["High"].idxmax().strftime("%Y-%m-%d")
            l_dt = d["Low"].idxmin().strftime("%Y-%m-%d")

            st.success(f"**{gt}** | CMP: {cur:.2f}")

            # --- THE CLEAN DASHBOARD LAYOUT ---
            colA, colB = st.columns(2)

            with colA:
                st.markdown("### 🔴 Levels from Top")
                st.caption(f"Major High: {h:.2f} ({h_dt})")
                lev_h = calculate_gann_levels(h)

                c1, c2 = st.columns(2)
                c1.metric("Resistance (360°)", f"{lev_h[8]:.2f}")
                c2.metric("Support (90°)", f"{lev_h[2]:.2f}")
                st.metric("Support (180°)", f"{lev_h[1]:.2f}")

            with colB:
                st.markdown("### 🟢 Levels from Bottom")
                st.caption(f"Major Low: {l:.2f} ({l_dt})")
                lev_l = calculate_gann_levels(l)

                c3, c4 = st.columns(2)
                c3.metric("Resistance (180°)", f"{lev_l[7]:.2f}")
                c4.metric("Resistance (360°)", f"{lev_l[8]:.2f}")
                st.metric("Major Support", f"{lev_l[4]:.2f}")

            st.divider()
            st.subheader("⏳ Gann Time Cycles (Watch Dates)")
            start = datetime.strptime(h_dt, "%Y-%m-%d")
            dates = []
            for d in [45, 90, 144, 180, 360]:
                fd = start + timedelta(days=d)
                if fd > datetime.now():
                    dates.append(f"**{d} Days:** {fd.strftime('%d %b %Y')}")
            for d in dates:
                st.write(d)

# TAB 7: HEATMAP
with tabs[6]:
    st.subheader("🗺️ Market Heatmap")
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
            "LT",
            "BAJFINANCE",
            "HCLTECH",
            "MARUTI",
            "SUNPHARMA",
            "ADANIENT",
            "KOTAKBANK",
            "TITAN",
            "TATAMOTORS",
            "ONGC",
            "AXISBANK",
            "NTPC",
            "ULTRACEMCO",
            "POWERGRID",
            "ADANIPORTS",
            "M&M",
            "WIPRO",
            "COALINDIA",
            "BAJAJ-AUTO",
            "ASIANPAINT",
            "JSWSTEEL",
            "NESTLEIND",
            "GRASIM",
            "LTIM",
            "SBILIFE",
            "TECHM",
            "HDFCLIFE",
            "BSOFT",
            "CIPLA",
            "TATASTEEL",
            "EICHERMOT",
            "DIVISLAB",
            "DRREDDY",
            "HEROMOTOCO",
            "TATACONSUM",
            "APOLLOHOSP",
            "BPCL",
            "BRITANNIA",
            "INDUSINDBK",
        ],
        "Nifty Bank": [
            "HDFCBANK",
            "ICICIBANK",
            "SBIN",
            "KOTAKBANK",
            "AXISBANK",
            "INDUSINDBK",
            "BANKBARODA",
            "PNB",
            "IDFCFIRSTB",
            "AUBANK",
        ],
        "Nifty IT": [
            "TCS",
            "INFY",
            "HCLTECH",
            "WIPRO",
            "TECHM",
            "LTIM",
            "PERSISTENT",
            "COFORGE",
            "MPHASIS",
            "LTTS",
        ],
    }
    sel = st.selectbox("View:", list(lists.keys()))
    if st.button("Generate Map"):
        ticks = [fix_ticker(x) for x in lists[sel]]
        with st.spinner("Building Map..."):
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
                fig.update_layout(height=650, margin=dict(t=30, l=10, r=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
