"""
EuroEquity Pro — Andrea Meschini, CFA
Applicazione professionale con dati reali da EODHD
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings("ignore")

# ─── CONFIGURAZIONE ───────────────────────────────────────────────
st.set_page_config(
    page_title="EuroEquity Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# EODHD API Key — sostituire con chiave a pagamento per uso commerciale
EODHD_KEY = "6a0826ce2e8a52.04646471"
EODHD_BASE = "https://eodhd.com/api"

# ─── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Outfit',sans-serif;}
.stApp{background-color:#07090d;color:#dde4f0;}
section[data-testid="stSidebar"]{background-color:#0d1017;border-right:1px solid #1e2840;}
[data-testid="metric-container"]{background:#0d1017;border:1px solid #1e2840;padding:12px 16px;border-radius:3px;}
[data-testid="metric-container"] label{color:#5a6880!important;font-size:10px!important;font-weight:700!important;letter-spacing:.1em!important;text-transform:uppercase!important;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#c8982a!important;font-size:1.3rem!important;font-weight:700!important;}
.stButton>button{background:rgba(200,152,42,0.12);border:1px solid rgba(200,152,42,0.3);color:#c8982a;font-weight:600;font-size:11px;}
.stButton>button:hover{background:rgba(200,152,42,0.25);}
.section-hdr{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#5a6880;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #1e2840;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
div[data-testid="stDataFrame"]{border:1px solid #1e2840;}
</style>
""", unsafe_allow_html=True)

# ─── EXCHANGE MAP ─────────────────────────────────────────────────
# EODHD exchange codes → display info
EXCHANGES = {
    "MI": {"flag":"🇮🇹","label":"Italy","market":"FTSE MIB — Borsa Italiana","exch_url":"https://www.borsaitaliana.it/borsa/azioni/scheda/{ticker}.html"},
    "XETRA": {"flag":"🇩🇪","label":"Germany","market":"DAX — Deutsche Börse","exch_url":"https://live.deutsche-boerse.com/equity/{slug}"},
    "PA": {"flag":"🇫🇷","label":"France","market":"CAC 40 — Euronext Paris","exch_url":"https://live.euronext.com/en/product/equities/{isin}-XPAR"},
    "AS": {"flag":"🇳🇱","label":"Netherlands","market":"AEX — Euronext Amsterdam","exch_url":"https://live.euronext.com/en/product/equities/{isin}-XAMS"},
    "MC": {"flag":"🇪🇸","label":"Spain","market":"IBEX 35 — BME Madrid","exch_url":"https://www.bolsasymercados.es/esp/empresas/cotizaciones/acciones/Ficha/{ticker}"},
    "BR": {"flag":"🇧🇪","label":"Belgium","market":"BEL 20 — Euronext Brussels","exch_url":"https://live.euronext.com/en/product/equities/{isin}-XBRU"},
    "LS": {"flag":"🇵🇹","label":"Portugal","market":"PSI — Euronext Lisbon","exch_url":"https://live.euronext.com/en/product/equities/{isin}-XLIS"},
    "VIE": {"flag":"🇦🇹","label":"Austria","market":"ATX — Wiener Börse","exch_url":"https://www.wienerborse.at/en/stock/{isin}/"},
    "HE": {"flag":"🇫🇮","label":"Finland","market":"OMX Helsinki — Nasdaq Nordic","exch_url":"https://www.nasdaqomxnordic.com/shares/microsite?Instrument={isin}"},
    "IR": {"flag":"🇮🇪","label":"Ireland","market":"ISEQ — Euronext Dublin","exch_url":"https://live.euronext.com/en/product/equities/{isin}-XDUB"},
    "AT": {"flag":"🇬🇷","label":"Greece","market":"ASE — Athens Stock Exchange","exch_url":"https://www.athexgroup.gr/en/web/guest/company-overview?securityCode={ticker}"},
}

# Index tickers on EODHD
INDEX_TICKERS = {
    "Euro Stoxx 50": "STOXX50E.INDX",
    "FTSE MIB": "FTSEMIB.MI",
    "DAX": "GDAXI.INDX",
    "CAC 40": "FCHI.INDX",
    "AEX": "AEX.AS",
    "IBEX 35": "IBEX.MC",
    "BEL 20": "BFX.BR",
    "PSI": "PSI20.INDX",
    "ATX": "ATX.VIE",
    "OMX Helsinki 25": "OMXH25.HE",
    "ISEQ": "ISEQ.IR",
    "ASE": "ATG.AT",
}

# ─── EODHD API FUNCTIONS ──────────────────────────────────────────

def eodhd_get(endpoint, params=None):
    """Make a call to EODHD API"""
    if params is None:
        params = {}
    params["api_token"] = EODHD_KEY
    params["fmt"] = "json"
    try:
        r = requests.get(f"{EODHD_BASE}/{endpoint}", params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=900, show_spinner=False)
def get_exchange_tickers(exchange_code):
    """Get all tickers listed on an exchange from EODHD"""
    data = eodhd_get(f"exchange-symbol-list/{exchange_code}", {"type": "CS"})
    if not data:
        return []
    return data


@st.cache_data(ttl=900, show_spinner=False)
def get_bulk_eod(exchange_code, date=None):
    """
    Get bulk end-of-day data for all stocks on an exchange.
    This is the most efficient EODHD endpoint — one call for the entire exchange.
    Returns: price, change, change_p, volume, market_cap for ALL stocks.
    """
    params = {}
    if date:
        params["date"] = date
    data = eodhd_get(f"eod-bulk-last-day/{exchange_code}", params)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_fundamentals(ticker_exchange):
    """
    Get full fundamental data for a single stock.
    ticker_exchange = 'ENI.MI'
    Returns: PE, PB, Beta, DivYield, ROE, D/E, EV/EBITDA, EPS fwd, etc.
    """
    data = eodhd_get(f"fundamentals/{ticker_exchange}", {"filter": "Highlights,Valuation,Technicals,SplitsDividends"})
    if not data:
        return {}

    h = data.get("Highlights", {})
    v = data.get("Valuation", {})
    t = data.get("Technicals", {})
    sd = data.get("SplitsDividends", {})

    return {
        "pe_t": h.get("PERatio"),
        "pe_f": h.get("ForwardPE"),
        "pb": v.get("PriceBookMRQ"),
        "ev_ebitda": v.get("EnterpriseValueEbitda"),
        "ev": v.get("EnterpriseValue"),
        "mktcap": h.get("MarketCapitalization", 0) / 1e9 if h.get("MarketCapitalization") else None,
        "roe": h.get("ReturnOnEquityTTM", 0) * 100 if h.get("ReturnOnEquityTTM") else None,
        "eps_t": h.get("EpsTtm"),
        "eps_f": h.get("EPSEstimateNextYear"),
        "div_yield": h.get("DividendYield", 0) * 100 if h.get("DividendYield") else None,
        "beta": t.get("Beta"),
        "revenue_growth": h.get("QuarterlyRevenueGrowthYOY", 0) * 100 if h.get("QuarterlyRevenueGrowthYOY") else None,
        "earnings_growth": h.get("QuarterlyEarningsGrowthYOY", 0) * 100 if h.get("QuarterlyEarningsGrowthYOY") else None,
    }


@st.cache_data(ttl=900, show_spinner=False)
def get_price_history(ticker_exchange, period_days=365):
    """Get historical EOD prices for momentum calculation"""
    from_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    data = eodhd_get(f"eod/{ticker_exchange}", {"from": from_date, "period": "d"})
    if not data:
        return None
    df = pd.DataFrame(data)
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


@st.cache_data(ttl=900, show_spinner=False)
def get_index_quote(index_ticker):
    """Get current quote for an index"""
    data = eodhd_get(f"real-time/{index_ticker}", {"s": index_ticker})
    if not data:
        return None
    if isinstance(data, list):
        data = data[0]
    return data


@st.cache_data(ttl=1800, show_spinner=False)
def build_exchange_screen(exchange_code, max_stocks=500):
    """
    Build complete screener data for an exchange.
    Uses bulk EOD for prices (1 API call) + fundamentals for top stocks.
    """
    # Step 1: Bulk EOD prices — all stocks, 1 API call
    bulk = get_bulk_eod(exchange_code)
    if bulk.empty:
        return pd.DataFrame()

    # Step 2: Get ticker list for names and sectors
    tickers = get_exchange_tickers(exchange_code)
    ticker_info = {t.get("Code", ""): t for t in tickers} if tickers else {}

    exch_meta = EXCHANGES.get(exchange_code, {})
    flag = exch_meta.get("flag", "")

    rows = []
    # Limit to avoid hitting free API limits — top stocks by market cap / volume
    bulk_sorted = bulk.nlargest(min(max_stocks, len(bulk)), "volume") if "volume" in bulk.columns else bulk.head(max_stocks)

    for _, row in bulk_sorted.iterrows():
        code = row.get("code", "")
        if not code:
            continue
        info = ticker_info.get(code, {})
        name = info.get("Name", code)
        # Skip ETFs, funds, warrants
        itype = info.get("Type", "")
        if itype in ["ETF", "Fund", "FUND", "Preferred Stock"]:
            continue

        px = row.get("close") or row.get("adjusted_close")
        prev = row.get("open")  # approximation; real prev close needs history
        change_pct = row.get("change_p")  # EODHD provides this directly

        rows.append({
            "EODHD_Ticker": f"{code}.{exchange_code}",
            "Ticker": f"{flag} {code}",
            "Company": name,
            "Country": exch_meta.get("label", ""),
            "Exchange": exchange_code,
            "Price": px,
            "1D %": change_pct,
            "Volume": row.get("volume"),
            "Market Cap €B": None,  # filled by fundamentals
            "P/E Trail.": None,
            "P/E Fwd 12M": None,
            "P/B": None,
            "EV/EBITDA": None,
            "EPS Gr Fwd 12M %": None,
            "Rev Gr Fwd 12M %": None,
            "D/E": None,
            "ROE %": None,
            "Div Yield % (ttm)": None,
            "Beta 1Y": None,
            "Mom 6M %": None,
            "Mom 12M %": None,
        })

    return pd.DataFrame(rows)


@st.cache_data(ttl=1800, show_spinner=False)
def enrich_with_fundamentals(df, max_enrich=100):
    """
    Add fundamentals to top stocks by volume.
    Limited to avoid exhausting free API calls.
    """
    if df.empty:
        return df

    df = df.copy()
    top = df.head(max_enrich)

    for idx, row in top.iterrows():
        tk = row["EODHD_Ticker"]
        try:
            fund = get_fundamentals(tk)
            if fund:
                df.at[idx, "Market Cap €B"] = fund.get("mktcap")
                df.at[idx, "P/E Trail."] = fund.get("pe_t")
                df.at[idx, "P/E Fwd 12M"] = fund.get("pe_f")
                df.at[idx, "P/B"] = fund.get("pb")
                df.at[idx, "EV/EBITDA"] = fund.get("ev_ebitda")
                df.at[idx, "ROE %"] = fund.get("roe")
                df.at[idx, "Div Yield % (ttm)"] = fund.get("div_yield")
                df.at[idx, "Beta 1Y"] = fund.get("beta")
                df.at[idx, "EPS Gr Fwd 12M %"] = fund.get("earnings_growth")
                df.at[idx, "Rev Gr Fwd 12M %"] = fund.get("revenue_growth")
        except Exception:
            pass

    return df


@st.cache_data(ttl=1800, show_spinner=False)
def get_momentum(ticker_exchange):
    """Calculate real 6M and 12M momentum from price history"""
    hist = get_price_history(ticker_exchange, 380)
    if hist is None or len(hist) < 5:
        return None, None
    closes = hist["adjusted_close"].dropna()
    n = len(closes)
    last = closes.iloc[-1]
    m6 = ((last / closes.iloc[max(0, n-126)]) - 1) * 100 if n >= 10 else None
    m12 = ((last / closes.iloc[0]) - 1) * 100 if n >= 20 else None
    return m6, m12


# ─── FORMATTING ───────────────────────────────────────────────────
def fp(v, d=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{'+'if v>=0 else ''}{v:.{d}f}%"

def fv(v, d=2, sfx=""):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:.{d}f}{sfx}"

def fc(v, inv=False):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "#dde4f0"
    if inv:
        return "#22d48a" if v < 0 else "#e84560" if v > 0 else "#dde4f0"
    return "#22d48a" if v > 0 else "#e84560" if v < 0 else "#dde4f0"


# ─── SIDEBAR ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="color:#c8982a;font-weight:700;font-size:15px;margin-bottom:4px;font-style:italic;">📊 EuroEquity Pro</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:9px;color:#5a6880;margin-bottom:16px;">Andrea Meschini, CFA</div>', unsafe_allow_html=True)

    page = st.radio("", [
        "🏠 Dashboard",
        "🔍 All Markets",
        "🇮🇹 Borsa Italiana",
        "🇩🇪 Deutsche Börse",
        "🇫🇷 Euronext Paris",
        "🇳🇱 Euronext Amsterdam",
        "🇪🇸 BME Madrid",
        "🇧🇪 Euronext Brussels",
        "🇵🇹 Euronext Lisbon",
        "🇦🇹 Wiener Börse",
        "🇫🇮 Nasdaq Helsinki",
        "🇮🇪 Euronext Dublin",
        "🇬🇷 Athens SE",
        "💼 Portafogli",
        "ℹ️ Info & Dati",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("""
    <div style="font-size:9px;color:#5a6880;line-height:1.6;">
    <b style="color:#22d48a;">● DATI REALI</b> · EODHD<br>
    Prezzi: 15 min delay<br>
    Fondamentali: end of day<br>
    Cache: 15 minuti
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Aggiorna dati"):
        st.cache_data.clear()
        st.rerun()

# ─── EXCHANGE ROUTER ──────────────────────────────────────────────
PAGE_TO_EXCHANGE = {
    "🇮🇹 Borsa Italiana": "MI",
    "🇩🇪 Deutsche Börse": "XETRA",
    "🇫🇷 Euronext Paris": "PA",
    "🇳🇱 Euronext Amsterdam": "AS",
    "🇪🇸 BME Madrid": "MC",
    "🇧🇪 Euronext Brussels": "BR",
    "🇵🇹 Euronext Lisbon": "LS",
    "🇦🇹 Wiener Börse": "VIE",
    "🇫🇮 Nasdaq Helsinki": "HE",
    "🇮🇪 Euronext Dublin": "IR",
    "🇬🇷 Athens SE": "AT",
}

# ─── SCREENER COMPONENT ───────────────────────────────────────────
def show_screener(df, title=""):
    """Render the full screener with filters and sortable table"""
    if df.empty:
        st.warning("Nessun dato disponibile. Verifica la connessione o riprova.")
        return

    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)
    st.caption(
        f"✅ **{len(df)}** titoli · Prezzi reali EODHD (15 min delay) · "
        "Beta = 1 anno vs indice locale · Div Yield = ultimi 12M / ultimo prezzo · "
        "P/E Fwd 12M = consenso analisti prossimi 12 mesi"
    )

    # ── FILTERS ──
    with st.expander("⚙️ Filtri", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            secs = ["Tutti"] + sorted(df["Company"].dropna().unique().tolist()[:50])
            pe_f_max = st.number_input("P/E Fwd max", 0.0, step=1.0, key=f"pe_{title}")
            pb_max = st.number_input("P/B max", 0.0, step=0.5, key=f"pb_{title}")
        with c2:
            beta_max = st.number_input("Beta max", 0.0, step=0.1, key=f"beta_{title}")
            div_min = st.number_input("Div Yield % min", 0.0, step=0.5, key=f"div_{title}")
            roe_min = st.number_input("ROE % min", 0.0, step=1.0, key=f"roe_{title}")
        with c3:
            mom12_min = st.number_input("Mom 12M % min", 0.0, step=5.0, key=f"m12_{title}")
            mom6_min = st.number_input("Mom 6M % min", 0.0, step=5.0, key=f"m6_{title}")
            price_min = st.number_input("Prezzo min €", 0.0, step=0.5, key=f"px_{title}")
        with c4:
            sort_col = st.selectbox("Ordina per", [
                "1D %", "Mom 12M %", "Mom 6M %", "P/E Fwd 12M",
                "Div Yield % (ttm)", "ROE %", "Beta 1Y", "Market Cap €B", "Volume"
            ], key=f"sort_{title}")
            sort_asc = st.checkbox("Crescente", False, key=f"asc_{title}")
            search = st.text_input("Cerca ticker/nome", "", key=f"search_{title}")

    # Apply filters
    fdf = df.copy()
    if search:
        q = search.lower()
        fdf = fdf[fdf["Ticker"].str.lower().str.contains(q) | fdf["Company"].str.lower().str.contains(q)]
    if pe_f_max > 0:
        fdf = fdf[fdf["P/E Fwd 12M"].isna() | (fdf["P/E Fwd 12M"] <= pe_f_max)]
    if pb_max > 0:
        fdf = fdf[fdf["P/B"].isna() | (fdf["P/B"] <= pb_max)]
    if beta_max > 0:
        fdf = fdf[fdf["Beta 1Y"].isna() | (fdf["Beta 1Y"] <= beta_max)]
    if div_min > 0:
        fdf = fdf[fdf["Div Yield % (ttm)"].notna() & (fdf["Div Yield % (ttm)"] >= div_min)]
    if roe_min > 0:
        fdf = fdf[fdf["ROE %"].notna() & (fdf["ROE %"] >= roe_min)]
    if mom12_min != 0:
        fdf = fdf[fdf["Mom 12M %"].notna() & (fdf["Mom 12M %"] >= mom12_min)]
    if mom6_min != 0:
        fdf = fdf[fdf["Mom 6M %"].notna() & (fdf["Mom 6M %"] >= mom6_min)]
    if price_min > 0:
        fdf = fdf[fdf["Price"].notna() & (fdf["Price"] >= price_min)]

    # Sort
    if sort_col in fdf.columns:
        fdf = fdf.sort_values(sort_col, ascending=sort_asc, na_position="last")

    st.caption(f"**{len(fdf)}** titoli dopo i filtri")

    # Format for display
    display_cols = ["Ticker","Company","Price","1D %","Market Cap €B",
                    "P/E Trail.","P/E Fwd 12M","P/B","EV/EBITDA",
                    "EPS Gr Fwd 12M %","Rev Gr Fwd 12M %","D/E","ROE %",
                    "Div Yield % (ttm)","Beta 1Y","Mom 6M %","Mom 12M %"]

    ddf = fdf[[c for c in display_cols if c in fdf.columns]].copy()

    # Format numbers
    for col in ["Price","Market Cap €B","P/E Trail.","P/E Fwd 12M","P/B","EV/EBITDA","D/E","Beta 1Y"]:
        if col in ddf.columns:
            ddf[col] = ddf[col].apply(lambda x: fv(x, 2) if col in ["Price","P/B","D/E","Beta 1Y"] else fv(x, 1))
    for col in ["1D %","EPS Gr Fwd 12M %","Rev Gr Fwd 12M %","ROE %","Div Yield % (ttm)","Mom 6M %","Mom 12M %"]:
        if col in ddf.columns:
            ddf[col] = ddf[col].apply(lambda x: fp(x))

    st.dataframe(ddf, use_container_width=True, hide_index=True, height=600,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width=90),
            "Company": st.column_config.TextColumn("Company", width=200),
        })

    # Exchange links
    with st.expander("🔗 Link borse ufficiali"):
        link_rows = []
        for _, row in fdf.head(50).iterrows():
            exch = EXCHANGES.get(row.get("Exchange",""), {})
            url = exch.get("exch_url","#").replace("{ticker}", row["Ticker"].split()[-1]).replace("{isin}","").replace("{slug}", row["Ticker"].split()[-1].lower())
            link_rows.append({"Ticker": row["Ticker"], "Company": row["Company"], "Link": url})
        ldf = pd.DataFrame(link_rows)
        ldf["Link"] = ldf["Link"].apply(lambda u: f'<a href="{u}" target="_blank">↗ Apri</a>')
        st.markdown(ldf.to_html(escape=False, index=False), unsafe_allow_html=True)


# ─── DASHBOARD ────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    # Header
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0d1017,#131720);border-bottom:1px solid #1e2840;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
        <span style="font-size:22px;font-weight:700;color:#c8982a;font-style:italic;">EuroEquity <span style="color:#dde4f0;">Pro</span></span>
        <span style="font-size:9px;background:rgba(34,212,138,0.1);color:#22d48a;border:1px solid rgba(34,212,138,0.3);padding:2px 8px;border-radius:2px;letter-spacing:.1em;font-weight:700;">● DATI REALI · EODHD</span>
        <span style="font-size:9px;background:rgba(90,104,128,0.2);color:#8a9ab8;border:1px solid rgba(90,104,128,0.3);padding:2px 8px;border-radius:2px;letter-spacing:.1em;">15 MIN DELAY</span>
        <span style="font-size:10px;color:#5a6880;margin-left:auto;">Andrea Meschini, CFA · andreameschini19@gmail.com</span>
    </div>
    """, unsafe_allow_html=True)

    # ── INDICI ──
    st.markdown('<div class="section-hdr">📈 Performance Indici — Dati Reali EODHD</div>', unsafe_allow_html=True)

    with st.spinner("Caricamento indici…"):
        idx_cols = st.columns(6)
        for i, (name, ticker) in enumerate(INDEX_TICKERS.items()):
            with idx_cols[i % 6]:
                q = get_index_quote(ticker)
                if q:
                    chg = q.get("change_p", 0) or 0
                    try:
                        chg = float(chg)
                    except (TypeError, ValueError):
                        chg = 0.0
                    px_val = q.get("close") or q.get("adjusted_close") or 0
                    try:
                        px_val = float(px_val)
                    except (TypeError, ValueError):
                        px_val = 0.0
                    color = "#22d48a" if chg >= 0 else "#e84560"
                    sign = "+" if chg >= 0 else ""
                    ts = q.get("timestamp", "")
                    if ts:
                        ts_str = datetime.fromtimestamp(ts).strftime("%H:%M") if isinstance(ts, (int,float)) else str(ts)[:5]
                    else:
                        ts_str = "—"
                    st.markdown(f"""
                    <div style="background:#0d1017;border:1px solid #1e2840;padding:9px 11px;border-radius:3px;margin-bottom:6px;">
                        <div style="font-size:8px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5a6880;margin-bottom:3px;">{name}</div>
                        <div style="font-family:'Fira Code',monospace;font-size:14px;font-weight:600;color:{color};">{sign}{chg:.2f}%</div>
                        <div style="font-family:'Fira Code',monospace;font-size:9px;color:#8a9ab8;">{px_val:,.1f} · {ts_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#0d1017;border:1px solid #1e2840;padding:9px 11px;border-radius:3px;margin-bottom:6px;">
                        <div style="font-size:8px;color:#5a6880;">{name}</div>
                        <div style="font-size:11px;color:#5a6880;">Caricamento…</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── CARICA DATI BORSA ITALIANA PER DASHBOARD ──
    st.markdown('<div class="section-hdr">📊 Borsa Italiana — Top Movers (dati reali)</div>', unsafe_allow_html=True)

    with st.spinner("Caricamento dati Borsa Italiana…"):
        mi_bulk = get_bulk_eod("MI")

    if not mi_bulk.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div style="font-size:9px;font-weight:700;letter-spacing:.1em;color:#22d48a;margin-bottom:6px;">🟢 TOP GAINER OGGI</div>', unsafe_allow_html=True)
            gainers = mi_bulk.nlargest(10, "change_p")[["code","close","change_p","volume"]].copy()
            gainers.columns = ["Ticker","Prezzo €","1D %","Volume"]
            gainers["1D %"] = gainers["1D %"].apply(lambda x: fp(x))
            gainers["Prezzo €"] = gainers["Prezzo €"].apply(lambda x: fv(x, 2))
            gainers["Volume"] = gainers["Volume"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
            st.dataframe(gainers, use_container_width=True, hide_index=True)

        with col2:
            st.markdown('<div style="font-size:9px;font-weight:700;letter-spacing:.1em;color:#e84560;margin-bottom:6px;">🔴 TOP LOSER OGGI</div>', unsafe_allow_html=True)
            losers = mi_bulk.nsmallest(10, "change_p")[["code","close","change_p","volume"]].copy()
            losers.columns = ["Ticker","Prezzo €","1D %","Volume"]
            losers["1D %"] = losers["1D %"].apply(lambda x: fp(x))
            losers["Prezzo €"] = losers["Prezzo €"].apply(lambda x: fv(x, 2))
            losers["Volume"] = losers["Volume"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
            st.dataframe(losers, use_container_width=True, hide_index=True)

        st.markdown(f"""
        <div style="font-size:9px;color:#5a6880;margin-top:8px;">
        📡 Fonte: EODHD · Borsa Italiana · {len(mi_bulk)} titoli caricati · Prezzi: 15 min delay
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("Dati Borsa Italiana non disponibili con la chiave gratuita. Con piano $20/mese tutti i dati sono accessibili.")

    # ── NOTA API ──
    st.markdown("---")
    st.info("""
    **ℹ️ Nota sulla chiave API gratuita**
    La chiave gratuita EODHD permette 20 chiamate API al giorno.
    Con il piano a **$20/mese** tutte le funzionalità sono disponibili:
    - Bulk EOD per tutti gli 11 mercati (migliaia di titoli)
    - Fondamentali completi (PE, PB, Beta, ROE, EV/EBITDA, etc.)
    - Storico prezzi 30 anni per calcolo momentum
    - EPS revision, stime analisti, dividendi storici
    """)


# ─── SINGLE EXCHANGE SCREENS ──────────────────────────────────────
elif page in PAGE_TO_EXCHANGE:
    exch_code = PAGE_TO_EXCHANGE[page]
    exch_meta = EXCHANGES.get(exch_code, {})
    flag = exch_meta.get("flag","")
    market = exch_meta.get("market","")

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0d1017,#131720);border-bottom:1px solid #1e2840;padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">
        <span style="font-size:28px;">{flag}</span>
        <div>
            <div style="font-size:16px;font-weight:700;color:#dde4f0;">{market}</div>
            <div style="font-size:10px;color:#5a6880;">Dati reali EODHD · Prezzi 15 min delay · Fondamentali end of day</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner(f"Caricamento titoli {market}… (può richiedere 30-60 secondi)"):
        df_exch = build_exchange_screen(exch_code, max_stocks=500)

    if df_exch.empty:
        st.error(f"""
        **Dati non disponibili per {market}**

        Con la chiave API gratuita EODHD (20 chiamate/giorno) i dati bulk per exchange
        potrebbero non essere accessibili.

        **Con il piano $20/mese:**
        - Tutti i titoli di ogni borsa europea
        - Bulk EOD: un'unica chiamata per tutti i titoli di un exchange
        - Fondamentali completi per ogni titolo
        - Storico prezzi per calcolo momentum reale

        Premi **Aggiorna dati** nella sidebar oppure abbonati su eodhd.com
        """)
    else:
        # Enrich top stocks with fundamentals
        with st.spinner(f"Caricamento fondamentali top titoli…"):
            df_exch = enrich_with_fundamentals(df_exch, max_enrich=50)

        show_screener(df_exch, title=f"{flag} {market} — {len(df_exch)} titoli")


# ─── ALL MARKETS ──────────────────────────────────────────────────
elif page == "🔍 All Markets":
    st.markdown("""
    <div style="padding:12px 0 16px;">
        <div style="font-size:18px;font-weight:700;color:#dde4f0;">🔍 All Eurozone Markets</div>
        <div style="font-size:10px;color:#5a6880;">Seleziona un mercato specifico dalla sidebar per caricare tutti i titoli. Con piano $20/mese: migliaia di titoli per ogni borsa.</div>
    </div>
    """, unsafe_allow_html=True)

    # Show summary table of all exchanges
    summary_data = []
    for code, meta in EXCHANGES.items():
        summary_data.append({
            "Exchange": f"{meta['flag']} {meta['market']}",
            "EODHD Code": code,
            "Titoli approssimativi": {
                "MI":"~400","XETRA":"~700","PA":"~800","AS":"~200",
                "MC":"~200","BR":"~150","LS":"~60","VIE":"~100",
                "HE":"~150","IR":"~50","AT":"~180"
            }.get(code,"~100"),
            "Link Borsa Ufficiale": meta['exch_url'].split('{')[0]
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

    st.info("👈 Seleziona una borsa specifica dalla sidebar sinistra per vedere tutti i titoli con dati reali.")


# ─── PORTFOLIOS ───────────────────────────────────────────────────
elif page == "💼 Portafogli":
    st.markdown('<div class="section-hdr">💼 Gestione Portafogli</div>', unsafe_allow_html=True)

    if "portfolios" not in st.session_state:
        st.session_state.portfolios = {
            "Portafoglio 1": {},
            "Portafoglio 2": {},
            "Portafoglio 3": {},
        }

    pf_names = list(st.session_state.portfolios.keys())
    c_sel, c_new = st.columns([3,2])
    with c_sel:
        active_pf = st.selectbox("Portafoglio attivo", pf_names)
    with c_new:
        new_pf_name = st.text_input("Nome nuovo portafoglio", placeholder="es. Growth EU")
        if st.button("+ Crea") and new_pf_name and len(st.session_state.portfolios) < 10:
            st.session_state.portfolios[new_pf_name] = {}
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-hdr">➕ Aggiungi titolo</div>', unsafe_allow_html=True)

    a1, a2, a3, a4, a5 = st.columns([2,1,1,1,1])
    with a1:
        ticker_input = st.text_input("Ticker EODHD", placeholder="es. ENI.MI oppure SAP.XETRA")
    with a2:
        exch_input = st.selectbox("Borsa", list(EXCHANGES.keys()))
    with a3:
        qty_input = st.number_input("Quantità", min_value=0.0, step=1.0)
    with a4:
        cost_input = st.number_input("Prezzo acquisto €", min_value=0.0, step=0.01)
    with a5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("+ Aggiungi"):
            full_ticker = ticker_input if "." in ticker_input else f"{ticker_input}.{exch_input}"
            if qty_input > 0 and cost_input > 0 and ticker_input:
                pf = st.session_state.portfolios[active_pf]
                if len(pf) >= 50:
                    st.error("Max 50 titoli per portafoglio")
                else:
                    pf[full_ticker] = {"qty": qty_input, "cost": cost_input, "exch": exch_input}
                    st.success(f"Aggiunto {full_ticker}")
                    st.rerun()

    # Show portfolio
    pf_data = st.session_state.portfolios.get(active_pf, {})
    if not pf_data:
        st.info("Nessun titolo. Aggiungi titoli sopra usando il codice EODHD (es. ENI.MI, SAP.XETRA, ASML.AS)")
    else:
        with st.spinner("Caricamento prezzi portafoglio…"):
            rows = []
            total_cost = 0
            total_curr = 0
            total_1d = 0

            for full_ticker, h in pf_data.items():
                # Get real-time quote from EODHD
                q = eodhd_get(f"real-time/{full_ticker}")
                if isinstance(q, list):
                    q = q[0] if q else {}
                if not q:
                    q = {}

                px = q.get("close") or q.get("adjusted_close") or h["cost"]
                chg_p = q.get("change_p", 0) or 0
                qty = h["qty"]
                cost_px = h["cost"]
                cost_val = qty * cost_px
                curr_val = qty * px
                pnl = curr_val - cost_val
                pnl_pct = pnl / cost_val * 100 if cost_val else 0
                pnl_1d = curr_val * chg_p / 100

                total_cost += cost_val
                total_curr += curr_val
                total_1d += pnl_1d

                rows.append({
                    "Ticker": full_ticker,
                    "Qty": qty,
                    "Costo €": cost_px,
                    "Val. Acquisto €": cost_val,
                    "Prezzo Attuale €": px,
                    "Val. Attuale €": curr_val,
                    "Peso %": None,
                    "P&L €": pnl,
                    "P&L %": pnl_pct,
                    "P&L Oggi €": pnl_1d,
                })

            total_pnl = total_curr - total_cost
            for r in rows:
                r["Peso %"] = r["Val. Attuale €"] / total_curr * 100 if total_curr else 0

        # KPIs
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Investito", f"€ {total_cost:,.0f}")
        k2.metric("Valore Attuale", f"€ {total_curr:,.0f}", fp((total_curr-total_cost)/total_cost*100) if total_cost else "—")
        k3.metric("P&L Totale", f"€ {total_pnl:+,.0f}", fp(total_pnl/total_cost*100) if total_cost else "—")
        k4.metric("P&L Oggi", f"€ {total_1d:+,.0f}")

        st.markdown("---")

        # Charts
        pf_df = pd.DataFrame(rows)
        ch1, ch2 = st.columns(2)
        with ch1:
            exch_data = pf_df.groupby(pf_df["Ticker"].str.split(".").str[-1])["Val. Attuale €"].sum().reset_index()
            exch_data.columns = ["Borsa","Valore €"]
            fig = px.pie(exch_data, values="Valore €", names="Borsa", title="Per Borsa",
                template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(paper_bgcolor="#0d1017",plot_bgcolor="#0d1017",font_color="#dde4f0",height=260,margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig, use_container_width=True)
        with ch2:
            fig2 = px.bar(pf_df.sort_values("P&L %",ascending=False), x="Ticker", y="P&L %",
                color="P&L %", color_continuous_scale=["#e84560","#131720","#22d48a"],
                color_continuous_midpoint=0, title="P&L % per titolo",
                template="plotly_dark")
            fig2.update_layout(paper_bgcolor="#0d1017",plot_bgcolor="#0d1017",font_color="#dde4f0",height=260,margin=dict(l=0,r=0,t=30,b=40),showlegend=False,coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

        # Table
        display_pf = pf_df.copy()
        for col in ["Costo €","Prezzo Attuale €"]:
            display_pf[col] = display_pf[col].apply(lambda x: fv(x,2))
        for col in ["Val. Acquisto €","Val. Attuale €","P&L €","P&L Oggi €"]:
            display_pf[col] = display_pf[col].apply(lambda x: f"€ {x:+,.0f}" if pd.notna(x) else "—")
        for col in ["Peso %","P&L %"]:
            display_pf[col] = display_pf[col].apply(lambda x: fp(x,1))
        display_pf["Qty"] = display_pf["Qty"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(display_pf, use_container_width=True, hide_index=True)

        # Remove button
        rm_sel = st.selectbox("Rimuovi titolo", list(pf_data.keys()))
        if st.button("🗑️ Rimuovi"):
            del st.session_state.portfolios[active_pf][rm_sel]
            st.rerun()


# ─── INFO ─────────────────────────────────────────────────────────
elif page == "ℹ️ Info & Dati":
    st.markdown('<div class="section-hdr">ℹ️ EuroEquity Pro — Info e Fonti Dati</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Analyst:** Andrea Meschini, CFA Charterholder Level III
        **Università:** Ca' Foscari, Venezia — Economia
        **Esperienza:**
        - JP Morgan London — Asst. Portfolio Manager (4 anni)
        - Zenit SGR — Gestore azionario fondo pensione (5 anni)
        **Sede:** Via Lorenzo Fava 24, 37139 Verona
        **Tel/WhatsApp:** +39 351 837 3385
        **Email:** andreameschini19@gmail.com
        """)
    with col2:
        st.markdown("""
        **Disclaimer legale:** I dati e gli strumenti forniti hanno scopo puramente informativo e non costituiscono consulenza personalizzata ai sensi della Direttiva MiFID II o del D.Lgs. 58/1998 (TUF). Andrea Meschini — Consulente Finanziario Autonomo, Albo OCF. I prezzi sono soggetti a ritardo di 15 minuti.
        """)

    st.markdown("---")
    st.markdown('<div class="section-hdr">📡 Fonti Dati e Costi</div>', unsafe_allow_html=True)

    data_table = pd.DataFrame([
        ["Prezzi EOD, variazione % giornaliera","EODHD Bulk EOD","$20/mese","1 chiamata API per tutti i titoli di un exchange"],
        ["Fondamentali (PE, PB, Beta, ROE, EV/EBITDA)","EODHD Fundamentals","$20/mese","Aggiornati ogni giorno a fine seduta"],
        ["Dividend yield (trailing 12M)","EODHD Fundamentals","$20/mese","Ultimo dividendo annuale / prezzo attuale"],
        ["EPS forward 12M e revisioni analisti","EODHD Estimates","$20/mese","Consenso analisti aggiornato"],
        ["Storico prezzi (momentum 6M, 12M)","EODHD Historical","$20/mese","30 anni di storia giornaliera"],
        ["Performance indici","EODHD Real-time","$20/mese","Euro Stoxx 50, FTSE MIB, DAX, ecc."],
        ["Hosting applicazione web","Railway.app","$5/mese","Server sempre online"],
        ["Dominio (es. euroequitypro.com)","Namecheap","~$12/anno",""],
        ["**TOTALE per sito pubblico**","","**~$26/mese**","+ licenza ridistribuzione dati"],
    ], columns=["Dato","Provider","Costo","Note"])
    st.dataframe(data_table, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="section-hdr">🔗 Borse Ufficiali — Link Diretti</div>', unsafe_allow_html=True)
    exch_table = pd.DataFrame([
        ["🇮🇹 Italy","Borsa Italiana","borsaitaliana.it/borsa/azioni"],
        ["🇩🇪 Germany","Deutsche Börse / Xetra","live.deutsche-boerse.com"],
        ["🇫🇷🇳🇱🇧🇪🇵🇹🇮🇪","Euronext (FR/NL/BE/PT/IE)","live.euronext.com"],
        ["🇪🇸 Spain","BME Madrid","bolsasymercados.es"],
        ["🇦🇹 Austria","Wiener Börse","wienerborse.at"],
        ["🇫🇮 Finland","Nasdaq Nordic Helsinki","nasdaqomxnordic.com"],
        ["🇬🇷 Greece","Athens Stock Exchange","athexgroup.gr"],
    ], columns=["Mercato","Borsa","URL"])
    st.dataframe(exch_table, use_container_width=True, hide_index=True)
