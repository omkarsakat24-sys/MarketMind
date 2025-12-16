import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import feedparser
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="MarketMind 2.0", page_icon="🧠", layout="wide")

# Custom CSS for "Bloomberg Dark" Look
st.markdown(
    """
<style>
    .stApp { background-color: #0e1117; color: #FAFAFA; }
    h1, h2, h3 { color: #00e676; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #00e676; }
    .stage-card { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00e676; }
</style>
""",
    unsafe_allow_html=True,
)

# --- 1. HELPER FUNCTIONS ---


def fix_ticker(symbol):
    """Smartly fixes ticker names."""
    s = symbol.strip().upper()
    name_map = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
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
        "ETERNAL": "ZOMATO",  # Fixed Alias
    }
    if s in name_map:
        s = name_map[s]
    if s.endswith(".NS") or s.endswith(".BO") or s.startswith("^"):
        return s
    return f"{s}.NS"


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


# --- COMMODITY LOGIC ---
def fetch_commodities():
    # Tickers for specific assets
    tickers = {
        "Brent Crude": "BZ=F",
        "Gold": "GC=F",
        "Silver (Solar/EV)": "SI=F",
        "Copper": "HG=F",
        "Aluminum": "ALI=F",
        "Steel (HRC)": "HRC=F",
        "Platinum": "PL=F",
        "Palladium": "PA=F",
        "USD/INR": "INR=X",
    }

    data = yf.download(
        list(tickers.values()),
        period="5d",
        interval="1d",
        group_by="ticker",
        progress=False,
    )

    results = []
    for name, ticker in tickers.items():
        try:
            df = data[ticker]
            if len(df) < 2:
                continue
            curr = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2]
            change = ((curr - prev) / prev) * 100

            # --- SMART IMPACT LOGIC ---
            impact = "Neutral"
            color = "gray"

            if "Crude" in name:
                if change > 1.5:
                    impact = "🔴 Bearish: PAINTS (Asian Paints), TYRES (MRF). 🟢 Bullish: ONGC."
                    color = "red"
                elif change < -1.5:
                    impact = "🟢 Bullish: PAINTS, TYRES, CEMENT. 🔴 Bearish: ONGC."
                    color = "green"

            elif "Gold" in name:
                if change > 1.0:
                    impact = "⚠️ Market Fear Increasing. Money moving to Safety."
                    color = "orange"

            elif "Silver" in name:
                if change > 2.0:
                    impact = "🔴 Cost Squeeze: SOLAR (Tata Power, Borosil), EV Batteries. 🟢 Bullish: MINERS (Hind Zinc)."
                    color = "red"
                elif change < -2.0:
                    impact = "🟢 Margin Boost: SOLAR & EV Manufacturers."
                    color = "green"

            elif "Aluminum" in name:
                if change > 1.5:
                    impact = "🟢 Bullish: Hindalco, Nalco. 🔴 Bearish: AUTO, FMCG (Foil/Packaging)."
                    color = "blue"

            elif "Steel" in name:
                if change > 1.5:
                    impact = "🟢 Bullish: Tata Steel, JSW. 🔴 Bearish: REALTY, AUTO (Input Cost)."
                    color = "blue"

            elif "Platinum" in name or "Palladium" in name:
                if change > 2.0:
                    impact = (
                        "🔴 Cost Spike: AUTO SECTOR (Catalytic Converters expensive)."
                    )
                    color = "red"

            elif "USD/INR" in name:
                if change > 0.3:
                    impact = "🟢 Bullish: IT (TCS, Infy), PHARMA (Exports). 🔴 Bearish: Importers."
                    color = "green"
                elif change < -0.3:
                    impact = "🔴 Bearish: IT, PHARMA. 🟢 Bullish: Importers (Oil, Electronics)."
                    color = "red"

            results.append([name, curr, change, impact, color])
        except:
            pass
    return results


# --- ADVANCED TRAP LOGIC ---
def analyze_smart_money(fii_L, fii_S, dii_L, dii_S, cli_L, cli_S):
    total_fii = fii_L + fii_S
    total_dii = dii_L + dii_S
    total_cli = cli_L + cli_S
    if total_fii == 0:
        return "WAITING", "gray", "Input Data", 0, 0, 0

    fii_bull = (fii_L / total_fii) * 100
    dii_bull = (dii_L / total_dii) * 100
    cli_bull = (cli_L / total_cli) * 100

    insti_trend = "NEUTRAL / FIGHT"
    if fii_bull > 60 and dii_bull > 60:
        insti_trend = "BULLISH"
    elif fii_bull < 40 and dii_bull < 40:
        insti_trend = "BEARISH"

    signal = "NEUTRAL"
    color = "gray"
    msg = "Market is finding direction."

    if insti_trend == "NEUTRAL / FIGHT":
        signal = "⚠️ CHOPPY / RANGEBOUND"
        color = "orange"
        msg = f"FIIs ({fii_bull:.0f}% Bull) and DIIs ({dii_bull:.0f}% Bull) are FIGHTING. Stuck in range. Option Sellers Day."
    elif insti_trend == "BULLISH":
        if cli_bull < 40:
            signal = "🟢 SMART RALLY (Buy Dips)"
            color = "green"
            msg = "Institutions United (Buy). Retail Scared."
        else:
            signal = "🟢 UPTREND (Crowded)"
            color = "#90ee90"
            msg = "Everyone is buying. Upside limited."
    elif insti_trend == "BEARISH":
        if cli_bull > 60:
            signal = "🔴 BRUTAL CRASH AHEAD"
            color = "red"
            msg = "Institutions Selling. Retail Buying (Trap)."
        else:
            signal = "🔴 DOWNTREND"
            color = "#ffcccb"
            msg = "Institutions Selling."

    return signal, color, msg, fii_bull, dii_bull, cli_bull


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
# REMOVED LIFECYCLE TAB (Tab 8)
tabs = st.tabs(
    [
        "🔥 Trap Detector",
        "🧭 Sector Compass",
        "💎 Stage 2",
        "🚀 Hype Meter",
        "📰 News",
        "📐 Gann",
        "🗺️ Heatmap",
        "🌎 Global Macro",
    ]
)

# TAB 1: TRAP DETECTOR
with tabs[0]:
    sig, col, txt, fp, dp, cp = analyze_smart_money(
        fii_L, fii_S, dii_L, dii_S, cli_L, cli_S
    )
    st.markdown(
        f"<h2 style='text-align: center; color: {col};'>{sig}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align: center; font-size:18px;'>{txt}</p>",
        unsafe_allow_html=True,
    )
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("FII View", f"{fp:.0f}% Bull")
        st.progress(int(fp))
    with c2:
        st.metric("DII View", f"{dp:.0f}% Bull")
        st.progress(int(dp))
    with c3:
        st.metric("Retail View", f"{cp:.0f}% Bull")
        st.progress(int(cp))
    st.divider()
    c4, c5 = st.columns(2)
    with c4:
        st.metric("Fear (VIX)", vix, delta_color="inverse")
    with c5:
        st.metric("Support (PCR)", pcr)

# TAB 2: SECTOR COMPASS
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
            fig.add_hline(100, line_dash="dot", line_color="gray")
            fig.add_vline(100, line_dash="dot", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)

            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.success(
                    "✅ **LEADING (Buy):** "
                    + ", ".join(df[df["Quad"] == "Leading"]["Sector"].tolist())
                )
                st.info(
                    "💎 **IMPROVING (Watch):** "
                    + ", ".join(df[df["Quad"] == "Improving"]["Sector"].tolist())
                )
            with c2:
                st.error(
                    "❌ **LAGGING (Avoid):** "
                    + ", ".join(df[df["Quad"] == "Lagging"]["Sector"].tolist())
                )
                st.warning(
                    "⚠️ **WEAKENING (Exit):** "
                    + ", ".join(df[df["Quad"] == "Weakening"]["Sector"].tolist())
                )

# TAB 3: STAGE 2 SCANNER
with tabs[2]:
    st.subheader("💎 The Stage 2 Hit List")
    u_t = st.text_area(
        "Enter Stocks to Check:",
        "RELIANCE, SBIN, TATAMOTORS, INFY, ITC, TATASTEEL, PERSISTENT",
    )
    if st.button("Run Stage 2 Analysis"):
        t_l = [fix_ticker(x) for x in u_t.split(",")]
        with st.spinner(f"Analyzing..."):
            data = get_stock_data(t_l)
            res = []
            for t in t_l:
                try:
                    df = data[t].copy()
                    if len(df) < 30:
                        continue
                    curr = df["Close"].iloc[-1]
                    ma = df["Close"].rolling(window=30).mean().iloc[-1]
                    dist = ((curr - ma) / ma) * 100
                    status = "❌ Stage 4 (Avoid)"
                    if dist > 20:
                        status = "⚠️ Overheated"
                    elif dist > 5:
                        status = "🚀 Strong Trend"
                    elif dist > 0:
                        status = "✅ Early Entry"
                    res.append(
                        [t.replace(".NS", ""), f"{curr:.2f}", f"{dist:.2f}%", status]
                    )
                except:
                    pass
            if res:
                st.dataframe(
                    pd.DataFrame(
                        res, columns=["Stock", "Price", "% Above 30W-MA", "Verdict"]
                    ),
                    use_container_width=True,
                )
            else:
                st.warning("No data found.")

# TAB 4: HYPE METER
with tabs[3]:
    sens = st.slider("Sensitivity", 0.5, 5.0, 1.0, 0.5)
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
                if fac > 5:
                    tag = "🚀 EXPLOSIVE"
                elif fac > 2:
                    tag = "🔥 HOT"
                elif fac > 1:
                    tag = "🌿 ACTIVE"
                else:
                    tag = "❄️ COLD"
                if fac > sens:
                    res.append([t, c, f"{fac:.1f}x", tag, dt.date()])
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

# TAB 6: GANN MASTER
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
            colA, colB = st.columns(2)
            with colA:
                st.markdown("### 🔴 Levels from Top")
                st.caption(f"Major High: {h:.2f} ({h_dt})")
                lev_h = calculate_gann_levels(h)
                c1, c2 = st.columns(2)
                c1.metric("Res (360°)", f"{lev_h[8]:.2f}")
                c2.metric("Sup (90°)", f"{lev_h[2]:.2f}")
            with colB:
                st.markdown("### 🟢 Levels from Bottom")
                st.caption(f"Major Low: {l:.2f} ({l_dt})")
                lev_l = calculate_gann_levels(l)
                c3, c4 = st.columns(2)
                c3.metric("Res (180°)", f"{lev_l[7]:.2f}")
                c4.metric("Sup (Base)", f"{lev_l[4]:.2f}")
            st.divider()
            st.subheader("⏳ Gann Time Cycles")
            start = datetime.strptime(h_dt, "%Y-%m-%d")
            dates = [
                f"**{d} Days:** {(start + timedelta(days=d)).strftime('%d %b %Y')}"
                for d in [45, 90, 144, 180, 360]
                if (start + timedelta(days=d)) > datetime.now()
            ]
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
        "Bank Nifty": [
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

# TAB 8: GLOBAL MACRO (Moved up to fill the spot)
with tabs[7]:
    st.subheader("🌎 Global Macro Intelligence")
    if st.button("Scan Global Assets"):
        with st.spinner("Analyzing Commodities..."):
            res = fetch_commodities()
            if res:
                for row in res:
                    name, price, chg, impact, col = row
                    with st.expander(f"{name}: {price:.2f} ({chg:+.2f}%)"):
                        st.markdown(f"**Impact:** :{col}[{impact}]")
            else:
                st.error("Data not available.")
