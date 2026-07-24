import re
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

st.set_page_config(page_title="ETF Holdings Explorer", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# Terminal styling — jet black, amber/orange monospace, no rounded corners.
# (identical system to the Ticker Co-Movement Analyzer)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'IBM Plex Mono', 'Consolas', monospace !important;
    }

    .stApp {
        background-color: #000000;
        color: #FF8C00;
    }
    section[data-testid="stSidebar"] { display: none; }
    header[data-testid="stHeader"] { background-color: #000000; }
    div.block-container { padding-top: 1.2rem; max-width: 1400px; }

    h1, h2, h3, h4, h5, h6 { color: #FF8C00 !important; letter-spacing: 0.5px; }
    p, span, label, .stMarkdown, .stCaption { color: #FFB84D !important; }

    .term-subtitle {
        color: #7A5A2E !important;
        font-size: 0.78rem;
        letter-spacing: 1px;
        margin-top: -6px;
        margin-bottom: 10px;
    }

    .term-title {
        color: #FF8C00 !important;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 2.4rem;
        letter-spacing: 0.5px;
        margin-top: 0.6em;
        margin-bottom: 6px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
        background-color: #050505 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { border-radius: 0px !important; }

    .term-label {
        color: #FF8C00 !important;
        font-size: 0.7rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 2px;
    }

    .stTextInput input {
        background-color: #000000 !important;
        color: #FF8C00 !important;
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 600;
        caret-color: #FF8C00;
    }
    .stTextInput input:focus {
        box-shadow: 0 0 0 1px #FF8C00 !important;
        border: 1px solid #FFB84D !important;
    }

    .stDateInput input {
        background-color: #000000 !important;
        color: #FF8C00 !important;
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 600;
    }
    div[data-baseweb="calendar"] { background-color: #000000 !important; }

    .stButton button {
        background-color: #000000;
        color: #FF8C00;
        border: 1px solid #FF8C00;
        border-radius: 0px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        letter-spacing: 1px;
        width: 100%;
        transition: none;
    }
    .stButton button:hover {
        background-color: #FF8C00;
        color: #000000;
        border: 1px solid #FF8C00;
    }

    div[data-testid="stMetric"] {
        background-color: #050505;
        border: 1px solid #FF8C00;
        padding: 10px 14px;
    }
    div[data-testid="stMetricLabel"] {
        color: #FF8C00 !important;
        font-size: 0.7rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 700;
    }

    .streamlit-expanderHeader {
        background-color: #050505 !important;
        color: #FF8C00 !important;
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
    }
    div[data-testid="stExpander"] { border: none; }

    div[data-testid="stDataFrame"] { border: 1px solid #FF8C00; }

    div[data-testid="stAlert"] {
        background-color: #050505;
        color: #FF8C00;
        border: 1px solid #FF8C00;
        border-radius: 0px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Access control (identical scheme to the Ticker Co-Movement Analyzer)
# ---------------------------------------------------------------------------
DEFAULT_ALLOWED_USERS = {("augustine", "villalobos"), ("david", "villalobos")}

def get_allowed_users() -> set:
    try:
        configured = st.secrets.get("allowed_users", None)
    except Exception:
        configured = None
    if not configured:
        return DEFAULT_ALLOWED_USERS
    return {
        (entry["first_name"].strip().lower(), entry["last_name"].strip().lower())
        for entry in configured
    }


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def render_login():
    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        with st.container(border=True):
            st.markdown("### RESTRICTED ACCESS")
            st.caption("ENTER YOUR FIRST AND LAST NAME TO CONTINUE")
            with st.form("login_form"):
                first = st.text_input("First name", placeholder="FIRST NAME")
                last = st.text_input("Last name", placeholder="LAST NAME")
                submitted = st.form_submit_button("ACCESS TERMINAL", use_container_width=True)

            if submitted:
                key = (first.strip().lower(), last.strip().lower())
                if key in get_allowed_users() and first.strip() and last.strip():
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("ACCESS DENIED — NAME NOT RECOGNIZED.")


if not st.session_state.authenticated:
    st.markdown('<div class="term-title">ETF HOLDINGS EXPLORER</div>', unsafe_allow_html=True)
    st.markdown('<div class="term-subtitle">CREATED BY AUGUSTINE VILLALOBOS</div>', unsafe_allow_html=True)
    render_login()
    st.stop()

# ---------- Helpers ----------

RED = "#FF1E1E"
BLUE = "#1E90FF"

EXCLUDE_KEYWORDS = [
    "GOVERNMENT OBLIGATIONS", "MONEY MARKET", "CASH COLLATERAL",
    "TREASURY BILL", "REPURCHASE", "CASH & OTHER", "CASH AND OTHER",
]

STRIP_TOKENS = [
    "SWAP-GOLD-L", "SWAP GOLD L", "TOTAL RETURN SWAP", "SWAP", "TRS",
    "GOLD-L", "GOLD L",
]


def clean_company_name(raw_name: str) -> str:
    n = raw_name.upper()
    for tok in STRIP_TOKENS:
        n = n.replace(tok, " ")
    n = re.sub(r"\b\d{6,}\b", " ", n)          # drop long numeric IDs
    n = re.sub(r"\b(NM|GS|LP|LTD|PLC)\b", " ", n)
    n = re.sub(r"[-]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n.title()


def is_equity_like(raw_name: str) -> bool:
    n = raw_name.upper()
    return not any(kw in n for kw in EXCLUDE_KEYWORDS)


def pick_symbol(symbols) -> str:
    plain = [s for s in symbols if isinstance(s, str) and re.fullmatch(r"[A-Z.]{1,6}", s.strip())]
    if plain:
        return sorted(plain, key=len)[0]
    return str(symbols[0])


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_holdings(etf_ticker: str) -> pd.DataFrame:
    t = yf.Ticker(etf_ticker)
    try:
        raw = t.funds_data.top_holdings
    except Exception:
        return pd.DataFrame()
    if raw is None or raw.empty:
        return pd.DataFrame()

    df = raw.reset_index()
    df.columns = [str(c).strip() for c in df.columns]
    # normalize expected column names across yfinance versions
    rename_map = {}
    for c in df.columns:
        cl = c.lower()
        if "symbol" in cl:
            rename_map[c] = "Symbol"
        elif "name" in cl:
            rename_map[c] = "Name"
        elif "percent" in cl or "weight" in cl:
            rename_map[c] = "Weight"
    df = df.rename(columns=rename_map)

    required = {"Symbol", "Name", "Weight"}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
    df = df.dropna(subset=["Weight"])
    if df["Weight"].max() <= 1.0:
        df["Weight"] = df["Weight"] * 100

    df = df[df["Name"].apply(is_equity_like)]
    if df.empty:
        return df

    df["clean_name"] = df["Name"].apply(clean_company_name)

    rows = []
    for name, g in df.groupby("clean_name"):
        weight = g["Weight"].sum()
        symbol = pick_symbol(list(g["Symbol"]))
        rows.append({"Name": name, "Symbol": symbol, "Weight": weight})

    out = pd.DataFrame(rows).sort_values("Weight", ascending=False).reset_index(drop=True)
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(ticker: str, start: date, end: date) -> pd.Series:
    df = yf.download(ticker, start=start, end=end + timedelta(days=1),
                      progress=False, auto_adjust=True)
    if df.empty:
        return pd.Series(dtype=float)
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.name = ticker
    return close


def make_chart(series: pd.Series, label: str, color: str, height: int, chart_title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values, name=label, mode="lines",
        line=dict(color=color, width=2.2)
    ))
    fig.update_layout(
        title=dict(text=chart_title, font=dict(color="#FF8C00", family="IBM Plex Mono", size=13)),
        xaxis=dict(color="#FF8C00", gridcolor="#2a2a2a", griddash="dot",
                   showline=True, linecolor="#FF8C00"),
        yaxis=dict(title="PRICE", color="#FF8C00", gridcolor="#2a2a2a", griddash="dot",
                   showline=True, linecolor="#FF8C00"),
        showlegend=False,
        hovermode="x unified",
        height=height,
        margin=dict(l=50, r=20, t=40, b=30),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(family="IBM Plex Mono", color="#FF8C00"),
    )
    return fig


# ---------- Header ----------

st.markdown('<div class="term-title">ETF HOLDINGS EXPLORER</div>', unsafe_allow_html=True)
st.markdown('<div class="term-subtitle">CREATED BY AUGUSTINE VILLALOBOS</div>', unsafe_allow_html=True)
st.caption("ETF TICKER  |  CUSTOM DATE RANGE  |  TOP HOLDINGS BY WEIGHT  |  DATA VIA YAHOO FINANCE")

# ---------- Top command bar ----------

default_start = date(date.today().year, 1, 1)  # YTD
default_end = date.today()

with st.container(border=True):
    c1, c2, c3, c4 = st.columns([1.3, 1, 1, 0.8])

    with c1:
        st.markdown('<div class="term-label">ETF TICKER</div>', unsafe_allow_html=True)
        etf_raw = st.text_input("ETF ticker", value="QQQ", label_visibility="collapsed")
    with c2:
        st.markdown('<div class="term-label">START DATE</div>', unsafe_allow_html=True)
        start_date = st.date_input("Start date", value=default_start,
                                    max_value=default_end, label_visibility="collapsed")
    with c3:
        st.markdown('<div class="term-label">END DATE</div>', unsafe_allow_html=True)
        end_date = st.date_input("End date", value=default_end,
                                  max_value=default_end, label_visibility="collapsed")
    with c4:
        st.markdown('<div class="term-label">&nbsp;</div>', unsafe_allow_html=True)
        run = st.button("ANALYZE", type="primary", use_container_width=True)

    st.caption("SHOWS YAHOO FINANCE'S TOP HOLDINGS FOR THE FUND — NOT ALWAYS THE FULL HOLDINGS LIST")

st.write("")

# ---------- Main logic ----------

if run:
    if start_date >= end_date:
        st.error("START DATE MUST BE BEFORE END DATE.")
        st.stop()

    etf_ticker = etf_raw.strip().upper()
    if not etf_ticker:
        st.error("PLEASE ENTER AN ETF TICKER.")
        st.stop()

    with st.spinner(f"FETCHING {etf_ticker} PRICE HISTORY..."):
        etf_prices = fetch_prices(etf_ticker, start_date, end_date)

    if etf_prices.empty:
        st.error(f"NO PRICE DATA FOR '{etf_ticker}'. CHECK TICKER SYMBOL.")
        st.stop()

    with st.spinner(f"FETCHING HOLDINGS FOR {etf_ticker}..."):
        holdings = fetch_holdings(etf_ticker)

    st.markdown(f"### {etf_ticker} — {start_date} TO {end_date}")
    st.plotly_chart(
        make_chart(etf_prices, etf_ticker, RED, 550, f"{etf_ticker} PRICE"),
        use_container_width=True,
    )

    if holdings.empty:
        st.info(f"NO HOLDINGS DATA AVAILABLE FOR '{etf_ticker}' VIA YAHOO FINANCE.")
        st.stop()

    st.markdown("### HOLDINGS BY WEIGHT")
    display_holdings = holdings.copy()
    display_holdings["Weight"] = display_holdings["Weight"].map(lambda w: f"{w:.2f}%")
    display_holdings = display_holdings[["Symbol", "Name", "Weight"]]
    st.dataframe(display_holdings, use_container_width=True, hide_index=True)

    top8 = holdings.head(8).reset_index(drop=True)

    st.markdown("### TOP HOLDINGS — PRICE CHARTS")
    mini_height = int(550 * 0.5)

    with st.spinner("FETCHING TOP HOLDING PRICE HISTORY..."):
        holding_series = {}
        for _, row in top8.iterrows():
            sym = row["Symbol"]
            series = fetch_prices(sym, start_date, end_date)
            holding_series[sym] = (series, row["Name"], row["Weight"])

    for i in range(0, len(top8), 2):
        cols = st.columns(2)
        pair = top8.iloc[i:i + 2]
        for col, (_, row) in zip(cols, pair.iterrows()):
            sym = row["Symbol"]
            series, name, weight = holding_series[sym]
            with col:
                if series.empty:
                    st.warning(f"NO PRICE DATA FOR '{sym}' ({name}).")
                else:
                    title = f"{sym} — {name.upper()} ({weight:.2f}%)"
                    st.plotly_chart(
                        make_chart(series, sym, BLUE, mini_height, title),
                        use_container_width=True,
                    )

else:
    st.info("ENTER AN ETF TICKER AND A DATE RANGE ABOVE, THEN PRESS ANALYZE.")
