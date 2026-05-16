"""
EuroEquity Pro — Andrea Meschini, CFA
Professional European equity research platform — real data via EODHD
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EuroEquity Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

EODHD_KEY  = "6a0826ce2e8a52.04646471"
EODHD_BASE = "https://eodhd.com/api"
ITALIAN_ISIN_PREFIX = "IT"

# ──────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────
EXCHANGES = {
    "MI":    {"flag":"🇮🇹","label":"Italy",       "market":"FTSE MIB — Borsa Italiana"},
    "XETRA":{"flag":"🇩🇪","label":"Germany",     "market":"DAX — Deutsche Börse"},
    "PA":   {"flag":"🇫🇷","label":"France",      "market":"CAC 40 — Euronext Paris"},
    "AS":   {"flag":"🇳🇱","label":"Netherlands", "market":"AEX — Euronext Amsterdam"},
    "MC":   {"flag":"🇪🇸","label":"Spain",       "market":"IBEX 35 — BME Madrid"},
    "BR":   {"flag":"🇧🇪","label":"Belgium",     "market":"BEL 20 — Euronext Brussels"},
    "LS":   {"flag":"🇵🇹","label":"Portugal",    "market":"PSI — Euronext Lisbon"},
    "VI":   {"flag":"🇦🇹","label":"Austria",     "market":"ATX — Wiener Börse"},
    "HE":   {"flag":"🇫🇮","label":"Finland",     "market":"OMX Helsinki — Nasdaq Nordic"},
    "IR":   {"flag":"🇮🇪","label":"Ireland",     "market":"ISEQ — Euronext Dublin"},
    "AT":   {"flag":"🇬🇷","label":"Greece",      "market":"ASE — Athens Stock Exchange"},
}

INDEX_TICKERS = {
    "Euro Stoxx 50":     "STOXX50E.INDX",
    "FTSE MIB":          "FTSEMIB.INDX",
    "FTSE MIB All Share":"ITLMS.INDX",
    "DAX":               "GDAXI.INDX",
    "CAC 40":            "FCHI.INDX",
    "AEX":               "AEX.INDX",
    "IBEX 35":           "IBEX.INDX",
    "BEL 20":            "BFX.INDX",
    "PSI":               "PSI20.INDX",
    "ATX":               "ATX.VI",
    "OMX Helsinki 25":   "OMXH25.HE",
    "ISEQ":              "ISEQ.IR",
    "ASE":               "ATG.AT",
}

PAGE_TO_EXCHANGE = {
    "🇮🇹 Borsa Italiana":    "MI",
    "🇩🇪 Deutsche Börse":    "XETRA",
    "🇫🇷 Euronext Paris":    "PA",
    "🇳🇱 Euronext Amsterdam":"AS",
    "🇪🇸 BME Madrid":        "MC",
    "🇧🇪 Euronext Brussels": "BR",
    "🇵🇹 Euronext Lisbon":   "LS",
    "🇦🇹 Wiener Börse":      "VI",
    "🇫🇮 Nasdaq Helsinki":   "HE",
    "🇮🇪 Euronext Dublin":   "IR",
    "🇬🇷 Athens SE":         "AT",
}

def guess_sector(name):
    n = (name or "").lower()
    if any(x in n for x in ["bank","banco","bancaire","banca","credit","finansb","finanziario","financ"]):
        return "Financials"
    if any(x in n for x in ["insur","assur","versicher","assicuraz"]):
        return "Insurance"
    if any(x in n for x in ["pharma","bio","medic","health","sanit","gesundh","sante"]):
        return "Health Care"
    if any(x in n for x in ["tech","software","digital","data","cloud","semi","chips","it ","siemens","sap","asm","asml"]):
        return "Technology"
    if any(x in n for x in ["auto","motor","volkswagen","bmw","mercedes","stellantis","ferrari","renault","peugeot"]):
        return "Consumer Discretionary"
    if any(x in n for x in ["food","beverage","luxury","retail","unilever","lvmh","nestl","ferrero","barilla"]):
        return "Consumer Staples"
    if any(x in n for x in ["energy","eni","total","repsol","bp ","shell","oil","gas","petro"]):
        return "Energy"
    if any(x in n for x in ["material","steel","mining","chemical","basf","linde","akzo","solvay","arcelormitta"]):
        return "Materials"
    if any(x in n for x in ["telecom","telekom","telefonica","orange","vodafone","tim ","bte","bt "]):
        return "Communication"
    if any(x in n for x in ["utility","enel","endesa","rwe","e.on","engie","a2a","hera","iren"]):
        return "Utilities"
    if any(x in n for x in ["real estate","realty","immobil","unibail","coima","land","property"]):
        return "Real Estate"
    if any(x in n for x in ["airbus","safran","rolls","defense","rheinm","industrial","siemens energy","scheidt"]):
        return "Industrials"
    return "Other"

# ──────────────────────────────────────────────────────────────────
# API FUNCTIONS
# ──────────────────────────────────────────────────────────────────
def eodhd_get(endpoint, params=None):
    if params is None:
        params = {}
    params["api_token"] = EODHD_KEY
    params["fmt"]       = "json"
    try:
        r = requests.get(f"{EODHD_BASE}/{endpoint}", params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=900, show_spinner=False)
def get_exchange_tickers(exchange_code):
    data = eodhd_get(f"exchange-symbol-list/{exchange_code}", {"type": "common_stock"})
    return data or []


@st.cache_data(ttl=900, show_spinner=False)
def get_bulk_eod(exchange_code):
    data = eodhd_get(f"eod-bulk-last-day/{exchange_code}")
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


@st.cache_data(ttl=900, show_spinner=False)
def get_italian_stocks_from_xetra():
    bulk    = get_bulk_eod("XETRA")
    tickers = get_exchange_tickers("XETRA")
    if bulk.empty or not tickers:
        return pd.DataFrame(), {}
    ticker_info   = {t.get("Code",""): t for t in tickers}
    italian_codes = {t.get("Code","") for t in tickers
                     if (t.get("ISIN") or "").startswith(ITALIAN_ISIN_PREFIX)}
    if "code" not in bulk.columns:
        return pd.DataFrame(), ticker_info
    return bulk[bulk["code"].isin(italian_codes)].copy(), ticker_info


@st.cache_data(ttl=3600, show_spinner=False)
def get_fundamentals(ticker_exchange):
    data = eodhd_get(f"fundamentals/{ticker_exchange}",
                     {"filter":"Highlights,Valuation,Technicals,SplitsDividends"})
    if not data:
        return {}
    h = data.get("Highlights", {}) or {}
    v = data.get("Valuation",   {}) or {}
    t = data.get("Technicals",  {}) or {}
    def sm(val, m):
        try: return float(val)*m if val is not None else None
        except: return None
    def sd(val, d):
        try: return float(val)/d if val is not None and d else None
        except: return None
    return {
        "pe_t":           h.get("PERatio"),
        "pe_f":           h.get("ForwardPE"),
        "pb":             v.get("PriceBookMRQ"),
        "ev_ebitda":      v.get("EnterpriseValueEbitda"),
        "mktcap":         sd(h.get("MarketCapitalization"), 1e9),
        "roe":            sm(h.get("ReturnOnEquityTTM"), 100),
        "div_yield":      sm(h.get("DividendYield"), 100),
        "beta":           t.get("Beta"),
        "earnings_growth":sm(h.get("QuarterlyEarningsGrowthYOY"), 100),
        "revenue_growth": sm(h.get("QuarterlyRevenueGrowthYOY"), 100),
        "eps_t":          h.get("EpsTtm"),
        "eps_f":          h.get("EPSEstimateNextYear"),
    }


@st.cache_data(ttl=900, show_spinner=False)
def get_price_history(ticker_exchange, period_days=400):
    from_date = (datetime.now()-timedelta(days=period_days)).strftime("%Y-%m-%d")
    data = eodhd_get(f"eod/{ticker_exchange}", {"from":from_date,"period":"d"})
    if not data:
        return None
    df = pd.DataFrame(data)
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")


@st.cache_data(ttl=900, show_spinner=False)
def get_index_quote(index_ticker):
    data = eodhd_get(f"real-time/{index_ticker}", {"s":index_ticker})
    if not data:
        return None
    return data[0] if isinstance(data, list) else data


# ──────────────────────────────────────────────────────────────────
# BUILD EXCHANGE DATAFRAME
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def build_exchange_df(exchange_code):
    exch_meta = EXCHANGES.get(exchange_code, {})
    flag      = exch_meta.get("flag","")

    if exchange_code == "MI":
        bulk, ticker_info = get_italian_stocks_from_xetra()
        if bulk.empty:
            return pd.DataFrame()
        source_exch = "XETRA"
    else:
        bulk        = get_bulk_eod(exchange_code)
        tickers     = get_exchange_tickers(exchange_code)
        ticker_info = {t.get("Code",""): t for t in tickers}
        source_exch = exchange_code

    if bulk.empty or "code" not in bulk.columns:
        return pd.DataFrame()

    rows = []
    for _, row in bulk.iterrows():
        code = row.get("code","")
        if not code:
            continue
        info  = ticker_info.get(code, {})
        itype = info.get("Type","")
        if itype in ["ETF","Fund","FUND","Preferred Stock"]:
            continue
        chg = row.get("change_p")
        try:
            chg = float(chg) if chg is not None else None
        except:
            chg = None

        name = info.get("Name", code)
        rows.append({
            "EODHD_Ticker": f"{code}.{source_exch}",
            "Ticker":       code,
            "Company":      name,
            "Country":      exch_meta.get("label",""),
            "Flag":         flag,
            "Exchange":     exchange_code,
            "Sector":       guess_sector(name),
            "Price":        row.get("close") or row.get("adjusted_close"),
            "1D %":         chg,
            "Volume":       row.get("volume"),
            "Market Cap €B":None, "P/E Trail.":None, "P/E Fwd 12M":None,
            "P/B":None, "EV/EBITDA":None, "ROE %":None,
            "Div Yield %":None, "Beta":None,
            "EPS Gr %":None, "Rev Gr %":None, "EPS Mom":None,
            "Mom 1W %":None, "Mom 1M %":None, "Mom 6M %":None, "Mom 12M %":None,
            "Value Score":None, "Growth Score":None,
        })
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────
# ENRICH — fundamentals + momentum + scores for ALL stocks
# ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def enrich_df(df, max_enrich=None):
    """Fetch fundamentals + momentum for all stocks (or top N by volume if max_enrich set)."""
    if df.empty:
        return df
    df = df.copy()
    if max_enrich is not None:
        top_idx = df.nlargest(min(max_enrich, len(df)), "Volume", keep="all").index
    else:
        top_idx = df.index  # ALL stocks

    for idx in top_idx:
        tk = df.at[idx, "EODHD_Ticker"]
        try:
            f = get_fundamentals(tk)
            if f:
                df.at[idx,"Market Cap €B"] = f.get("mktcap")
                df.at[idx,"P/E Trail."]    = f.get("pe_t")
                df.at[idx,"P/E Fwd 12M"]   = f.get("pe_f")
                df.at[idx,"P/B"]           = f.get("pb")
                df.at[idx,"EV/EBITDA"]     = f.get("ev_ebitda")
                df.at[idx,"ROE %"]         = f.get("roe")
                df.at[idx,"Div Yield %"]   = f.get("div_yield")
                df.at[idx,"Beta"]          = f.get("beta")
                df.at[idx,"EPS Gr %"]      = f.get("earnings_growth")
                df.at[idx,"Rev Gr %"]      = f.get("revenue_growth")
                ef = f.get("eps_f"); et = f.get("eps_t")
                if ef and et:
                    try:
                        ef, et = float(ef), float(et)
                        if et != 0:
                            df.at[idx,"EPS Mom"] = (ef - et) / abs(et) * 100
                    except:
                        pass
        except:
            pass

        try:
            hist = get_price_history(tk, 400)
            if hist is not None and len(hist) >= 5:
                closes = hist["adjusted_close"].dropna().values
                n      = len(closes)
                last   = closes[-1]
                if n >= 5:
                    df.at[idx,"Mom 1W %"]  = (last / closes[max(0,n-5)]  - 1) * 100
                if n >= 21:
                    df.at[idx,"Mom 1M %"]  = (last / closes[max(0,n-21)] - 1) * 100
                if n >= 126:
                    df.at[idx,"Mom 6M %"]  = (last / closes[max(0,n-126)]- 1) * 100
                if n >= 252:
                    df.at[idx,"Mom 12M %"] = (last / closes[max(0,n-252)]- 1) * 100
        except:
            pass

    # ── VALUE SCORE (per-exchange rank 1-100) ──
    def rank100(series):
        return series.rank(pct=True, na_option="keep") * 100

    def safe_inv(col):
        def _inv(x):
            try:
                v = float(x)
                return 1/v if v > 0 else None
            except:
                return None
        return col.apply(_inv)

    r_eyt = rank100(safe_inv(df["P/E Trail."]))
    r_eyf = rank100(safe_inv(df["P/E Fwd 12M"]))
    r_pb  = rank100(safe_inv(df["P/B"]))
    val_sum = r_eyt.add(r_eyf, fill_value=0).add(r_pb, fill_value=0)
    df["Value Score"] = rank100(val_sum).round(0)

    # ── GROWTH SCORE (per-exchange rank 1-100) ──
    r_epsg  = rank100(df["EPS Gr %"])
    r_revg  = rank100(df["Rev Gr %"])
    r_epsm  = rank100(df["EPS Mom"])
    mom12_1 = df["Mom 12M %"].sub(df["Mom 1M %"], fill_value=None)
    mom6_1w = df["Mom 6M %"].sub(df["Mom 1W %"],  fill_value=None)
    r_m12_1 = rank100(mom12_1)
    r_m6_1w = rank100(mom6_1w)
    grow_sum = (r_epsg.add(r_revg,  fill_value=0)
                      .add(r_epsm,  fill_value=0)
                      .add(r_m12_1, fill_value=0)
                      .add(r_m6_1w, fill_value=0))
    df["Growth Score"] = rank100(grow_sum).round(0)

    return df


# ──────────────────────────────────────────────────────────────────
# FORMATTING
# ──────────────────────────────────────────────────────────────────
def fp(v, d=1):
    if v is None: return "—"
    try:
        v = float(v)
        if np.isnan(v): return "—"
    except:
        return "—"
    return f"{'+'if v>=0 else ''}{v:.{d}f}%"

def fv(v, d=2):
    if v is None: return "—"
    try:
        v = float(v)
        if np.isnan(v): return "—"
    except:
        return "—"
    return f"{v:.{d}f}"


# ──────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="color:#c8982a;font-weight:700;font-size:15px;margin-bottom:4px;font-style:italic;">📊 EuroEquity Pro</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:9px;color:#5a6880;margin-bottom:16px;">Andrea Meschini, CFA</div>', unsafe_allow_html=True)

    page = st.radio("", [
        "🏠 Dashboard",
        "🌍 Eurozone Screen",
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
        "💼 Portfolios",
        "ℹ️ Info & Data",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div style="font-size:9px;color:#5a6880;line-height:1.6;"><b style="color:#22d48a;">● LIVE DATA</b> · EODHD<br>Prices: 15 min delay<br>Fundamentals: end of day<br>Cache: 15 min</div>', unsafe_allow_html=True)

    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()


# ──────────────────────────────────────────────────────────────────
# SCREENER COMPONENT
# ──────────────────────────────────────────────────────────────────
def show_screener(df, title="", exchange_code=""):
    if df.empty:
        st.warning("No data available. Check API connection or refresh.")
        return

    if exchange_code == "MI":
        st.info("ℹ️ **Borsa Italiana** — Italian stocks extracted from XETRA by Italian ISIN (IT*). Prices in EUR, aligned with Milan exchange.")

    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)
    st.caption(f"✅ **{len(df)}** stocks · EODHD real data (15 min delay) · All stocks enriched with fundamentals & momentum · Value & Growth scores ranked per country")

    with st.expander("⚙️ Filters", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            pe_f_max  = st.number_input("P/E Fwd max",    0.0, step=1.0, key=f"pe_{title[:10]}")
            pb_max    = st.number_input("P/B max",         0.0, step=0.5, key=f"pb_{title[:10]}")
            div_min   = st.number_input("Div Yield % min", 0.0, step=0.5, key=f"dv_{title[:10]}")
        with fc2:
            roe_min   = st.number_input("ROE % min",       0.0, step=1.0, key=f"roe_{title[:10]}")
            beta_max  = st.number_input("Beta max",        0.0, step=0.1, key=f"bt_{title[:10]}")
            price_min = st.number_input("Price min €",     0.0, step=0.5, key=f"px_{title[:10]}")
        with fc3:
            mom1m_min  = st.number_input("Mom 1M % min",  0.0, step=1.0, key=f"m1m_{title[:10]}")
            mom6m_min  = st.number_input("Mom 6M % min",  0.0, step=5.0, key=f"m6_{title[:10]}")
            mom12m_min = st.number_input("Mom 12M % min", 0.0, step=5.0, key=f"m12_{title[:10]}")
        with fc4:
            sectors  = ["All"] + sorted(df["Sector"].dropna().unique().tolist())
            sec_sel  = st.selectbox("Sector", sectors, key=f"sec_{title[:10]}")
            sort_col = st.selectbox("Sort by", [
                "1D %","Mom 12M %","Mom 6M %","Mom 1M %","Mom 1W %",
                "P/E Fwd 12M","Div Yield %","ROE %","Beta",
                "Market Cap €B","Volume","Value Score","Growth Score"
            ], key=f"srt_{title[:10]}")
            sort_asc = st.checkbox("Ascending", False, key=f"asc_{title[:10]}")
            search   = st.text_input("Search ticker / name", "", key=f"srch_{title[:10]}")

    fdf = df.copy()
    if search:
        q = search.lower()
        fdf = fdf[fdf["Ticker"].str.lower().str.contains(q, na=False) |
                  fdf["Company"].str.lower().str.contains(q, na=False)]
    if sec_sel != "All":
        fdf = fdf[fdf["Sector"] == sec_sel]
    if pe_f_max  > 0: fdf = fdf[fdf["P/E Fwd 12M"].isna() | (fdf["P/E Fwd 12M"] <= pe_f_max)]
    if pb_max    > 0: fdf = fdf[fdf["P/B"].isna()          | (fdf["P/B"]          <= pb_max)]
    if div_min   > 0: fdf = fdf[fdf["Div Yield %"].notna()  & (fdf["Div Yield %"]  >= div_min)]
    if roe_min   > 0: fdf = fdf[fdf["ROE %"].notna()        & (fdf["ROE %"]        >= roe_min)]
    if beta_max  > 0: fdf = fdf[fdf["Beta"].isna()          | (fdf["Beta"]         <= beta_max)]
    if price_min > 0: fdf = fdf[fdf["Price"].notna()        & (fdf["Price"]        >= price_min)]
    if mom1m_min > 0: fdf = fdf[fdf["Mom 1M %"].notna()     & (fdf["Mom 1M %"]     >= mom1m_min)]
    if mom6m_min > 0: fdf = fdf[fdf["Mom 6M %"].notna()     & (fdf["Mom 6M %"]     >= mom6m_min)]
    if mom12m_min> 0: fdf = fdf[fdf["Mom 12M %"].notna()    & (fdf["Mom 12M %"]    >= mom12m_min)]
    if sort_col in fdf.columns:
        fdf = fdf.sort_values(sort_col, ascending=sort_asc, na_position="last")

    st.caption(f"**{len(fdf)}** stocks after filters")

    COLS = ["Ticker","Company","Sector","Price","1D %",
            "Market Cap €B","P/E Trail.","P/E Fwd 12M","P/B","EV/EBITDA",
            "ROE %","Div Yield %","Beta",
            "EPS Gr %","Rev Gr %",
            "Mom 1W %","Mom 1M %","Mom 6M %","Mom 12M %",
            "Value Score","Growth Score"]
    ddf = fdf[[c for c in COLS if c in fdf.columns]].copy()

    for col in ["Price","Market Cap €B","P/E Trail.","P/E Fwd 12M","P/B","EV/EBITDA","Beta"]:
        if col in ddf.columns:
            ddf[col] = ddf[col].apply(lambda x: fv(x, 2 if col in ["Price","P/B","Beta"] else 1))
    for col in ["ROE %","Div Yield %","EPS Gr %","Rev Gr %",
                "1D %","Mom 1W %","Mom 1M %","Mom 6M %","Mom 12M %"]:
        if col in ddf.columns:
            ddf[col] = ddf[col].apply(fp)
    for col in ["Value Score","Growth Score"]:
        if col in ddf.columns:
            ddf[col] = ddf[col].apply(lambda x: f"{int(x)}" if pd.notna(x) and x == x else "—")

    st.dataframe(ddf, use_container_width=True, hide_index=True, height=550,
        column_config={
            "Ticker":       st.column_config.TextColumn("Ticker",  width=75),
            "Company":      st.column_config.TextColumn("Company", width=180),
            "Sector":       st.column_config.TextColumn("Sector",  width=130),
            "Value Score":  st.column_config.TextColumn("Value",   width=55),
            "Growth Score": st.column_config.TextColumn("Growth",  width=60),
        })

    # ── STOCK DETAIL ──
    st.markdown("---")
    st.markdown('<div class="section-hdr">📈 Stock Detail — Select a ticker to view chart & data</div>', unsafe_allow_html=True)
    ticker_options = fdf["Ticker"].tolist()
    if ticker_options:
        sel_ticker = st.selectbox(
            "Select ticker",
            ticker_options,
            format_func=lambda t: f"{t}  —  {fdf[fdf['Ticker']==t]['Company'].values[0] if not fdf[fdf['Ticker']==t].empty else ''}",
            key=f"detail_{title[:10]}"
        )
        sel_row = fdf[fdf["Ticker"] == sel_ticker]
        if not sel_row.empty:
            r        = sel_row.iloc[0]
            eodhd_tk = r["EODHD_Ticker"]

            c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)
            c1.metric("Price €",      fv(r.get("Price"),2))
            c2.metric("1D %",         fp(r.get("1D %")))
            c3.metric("P/E Trailing", fv(r.get("P/E Trail."),1))
            c4.metric("P/E Fwd 12M",  fv(r.get("P/E Fwd 12M"),1))
            c5.metric("P/B",          fv(r.get("P/B"),2))
            c6.metric("EV/EBITDA",    fv(r.get("EV/EBITDA"),1))
            c7.metric("Div Yield %",  fp(r.get("Div Yield %")))
            c8.metric("ROE %",        fp(r.get("ROE %")))

            d1,d2,d3,d4,d5,d6,d7,d8 = st.columns(8)
            d1.metric("Mkt Cap €B",  fv(r.get("Market Cap €B"),1))
            d2.metric("Beta",        fv(r.get("Beta"),2))
            d3.metric("EPS Gr %",    fp(r.get("EPS Gr %")))
            d4.metric("Rev Gr %",    fp(r.get("Rev Gr %")))
            d5.metric("Mom 1W",      fp(r.get("Mom 1W %")))
            d6.metric("Mom 1M",      fp(r.get("Mom 1M %")))
            d7.metric("Mom 12M",     fp(r.get("Mom 12M %")))
            vs = r.get("Value Score"); gs = r.get("Growth Score")
            vs_str = f"{int(vs)}" if pd.notna(vs) and vs == vs else "—"
            gs_str = f"{int(gs)}" if pd.notna(gs) and gs == gs else "—"
            d8.metric("Value / Growth", f"{vs_str} / {gs_str}")

            period_map = {"1Y": 365, "3Y": 3*365, "5Y": 5*365}
            period_sel = st.radio("Chart period", list(period_map.keys()), horizontal=True,
                                  key=f"cp_{title[:10]}")
            with st.spinner("Loading price chart…"):
                hist = get_price_history(eodhd_tk, period_map[period_sel])

            if hist is not None and not hist.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist["date"], y=hist["adjusted_close"],
                    mode="lines", name=sel_ticker,
                    line=dict(color="#c8982a", width=2)
                ))
                fig.update_layout(
                    title=f"{r['Company']} ({sel_ticker}) — {period_sel} price history",
                    xaxis_title="", yaxis_title="Price (EUR)",
                    template="plotly_dark",
                    paper_bgcolor="#0d1017", plot_bgcolor="#07090d",
                    font_color="#dde4f0", height=380,
                    margin=dict(l=0,r=0,t=40,b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Price history not available for this stock.")

            # Add to portfolio
            st.markdown("---")
            st.markdown('<div class="section-hdr">➕ Add to portfolio</div>', unsafe_allow_html=True)
            if "portfolios" not in st.session_state:
                st.session_state.portfolios = {
                    "Portfolio 1": {}, "Portfolio 2": {}, "Portfolio 3": {}
                }
            pa1,pa2,pa3,pa4 = st.columns([2,1,1,1])
            with pa1:
                pf_target = st.selectbox("Portfolio",
                    list(st.session_state.portfolios.keys()),
                    key=f"pf_{title[:10]}_{sel_ticker}")
            with pa2:
                qty_add  = st.number_input("Qty", min_value=0.0, step=1.0,
                                           key=f"qty_{title[:10]}_{sel_ticker}")
            with pa3:
                cost_add = st.number_input("Buy price €", min_value=0.0, step=0.01,
                                           value=float(r.get("Price") or 0),
                                           key=f"cost_{title[:10]}_{sel_ticker}")
            with pa4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Add", key=f"addpf_{title[:10]}_{sel_ticker}"):
                    if qty_add > 0 and cost_add > 0:
                        pf = st.session_state.portfolios[pf_target]
                        if len(pf) < 50:
                            pf[eodhd_tk] = {"qty": qty_add, "cost": cost_add}
                            st.success(f"Added {eodhd_tk} to {pf_target}")
                        else:
                            st.error("Max 50 stocks per portfolio")


# ──────────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0d1017,#131720);border-bottom:1px solid #1e2840;
    padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
        <span style="font-size:22px;font-weight:700;color:#c8982a;font-style:italic;">EuroEquity
        <span style="color:#dde4f0;">Pro</span></span>
        <span style="font-size:9px;background:rgba(34,212,138,0.1);color:#22d48a;
        border:1px solid rgba(34,212,138,0.3);padding:2px 8px;border-radius:2px;
        letter-spacing:.1em;font-weight:700;">● LIVE DATA · EODHD</span>
        <span style="font-size:9px;background:rgba(90,104,128,0.2);color:#8a9ab8;
        border:1px solid rgba(90,104,128,0.3);padding:2px 8px;border-radius:2px;">15 MIN DELAY</span>
        <span style="font-size:10px;color:#5a6880;margin-left:auto;">
        Andrea Meschini, CFA · andreameschini19@gmail.com</span>
    </div>
    """, unsafe_allow_html=True)

    # ── SEARCH BAR ──
    dash_search = st.text_input(
        "🔍 Search ticker or company name across all markets",
        placeholder="e.g. ENI, Volkswagen, ASML…"
    )

    # ── INDEX PERFORMANCE ──
    st.markdown('<div class="section-hdr">📈 Index Performance — Real Data EODHD</div>', unsafe_allow_html=True)
    with st.spinner("Loading indices…"):
        idx_cols = st.columns(7)
        for i, (name, ticker) in enumerate(INDEX_TICKERS.items()):
            with idx_cols[i % 7]:
                q = get_index_quote(ticker)
                if q:
                    chg = q.get("change_p", 0)
                    try:   chg = float(chg) if chg is not None else 0.0
                    except: chg = 0.0
                    px_val = q.get("close") or q.get("adjusted_close") or 0
                    try:   px_val = float(px_val)
                    except: px_val = 0.0
                    color = "#22d48a" if chg >= 0 else "#e84560"
                    sign  = "+" if chg >= 0 else ""
                    ts = q.get("timestamp", "")
                    try:   ts_str = datetime.fromtimestamp(int(ts)).strftime("%H:%M") if ts else "—"
                    except: ts_str = "—"
                    st.markdown(f"""
                    <div style="background:#0d1017;border:1px solid #1e2840;padding:9px 11px;
                    border-radius:3px;margin-bottom:6px;">
                        <div style="font-size:7px;font-weight:700;letter-spacing:.08em;
                        text-transform:uppercase;color:#5a6880;margin-bottom:2px;">{name}</div>
                        <div style="font-family:'Fira Code',monospace;font-size:13px;
                        font-weight:600;color:{color};">{sign}{chg:.2f}%</div>
                        <div style="font-family:'Fira Code',monospace;font-size:8px;
                        color:#8a9ab8;">{px_val:,.1f} · {ts_str}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#0d1017;border:1px solid #1e2840;padding:9px 11px;
                    border-radius:3px;margin-bottom:6px;">
                        <div style="font-size:7px;color:#5a6880;">{name}</div>
                        <div style="font-size:10px;color:#5a6880;">N/A</div>
                    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── LOAD ALL MARKETS (prices only, fast) ──
    @st.cache_data(ttl=1800, show_spinner=False)
    def load_all_markets_prices():
        frames = []
        for code in EXCHANGES:
            df_ex = build_exchange_df(code)
            if not df_ex.empty:
                frames.append(df_ex)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # ── LOAD ENRICHED SAMPLE FOR KPIs (top 50 per exchange for speed) ──
    @st.cache_data(ttl=3600, show_spinner=False)
    def load_dashboard_enriched():
        frames = []
        for code in EXCHANGES:
            df_ex = build_exchange_df(code)
            if not df_ex.empty:
                df_ex = enrich_df(df_ex, max_enrich=50)
                frames.append(df_ex)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    with st.spinner("Loading all Eurozone market prices…"):
        all_df = load_all_markets_prices()

    with st.spinner("Loading enriched data for KPIs (top 50 per market)…"):
        enriched = load_dashboard_enriched()

    if not all_df.empty:
        total_stocks = len(all_df)
        ew_12m   = enriched["Mom 12M %"].dropna().mean() if not enriched.empty else None
        div3_cnt = int((enriched["Div Yield %"].dropna() > 3).sum()) if not enriched.empty else 0
        eps_cnt  = int(enriched["EPS Gr %"].notna().sum()) if not enriched.empty else 0

        kk = st.columns(4)
        kk[0].metric("Total Stocks — All Markets",  f"{total_stocks:,}")
        kk[1].metric("Eq. Weighted 12M Return",     fp(ew_12m) if ew_12m is not None else "N/A")
        kk[2].metric("Stocks with EPS Growth Data", f"{eps_cnt:,}")
        kk[3].metric("Stocks Div Yield > 3%",        f"{div3_cnt:,}")

        st.markdown("---")

        # ── SEARCH RESULTS ──
        if dash_search:
            q = dash_search.lower()
            matches = all_df[
                all_df["Ticker"].str.lower().str.contains(q, na=False) |
                all_df["Company"].str.lower().str.contains(q, na=False)
            ].head(30)
            if not matches.empty:
                st.markdown(f'<div class="section-hdr">🔍 Search results for "{dash_search}" — {len(matches)} stocks found</div>', unsafe_allow_html=True)
                disp = matches[["Flag","Ticker","Company","Sector","Country","Price","1D %","Volume"]].copy()
                disp["Price"]  = disp["Price"].apply(lambda x: fv(x,2))
                disp["1D %"]   = disp["1D %"].apply(fp)
                disp["Volume"] = disp["Volume"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
                st.dataframe(disp, use_container_width=True, hide_index=True)
                st.markdown("---")
            else:
                st.warning(f"No stocks found for '{dash_search}'")
                st.markdown("---")

        # ── TOP 10 GAINERS & LOSERS ──
        all_df["_chg"] = pd.to_numeric(all_df["1D %"], errors="coerce")
        valid = all_df[all_df["_chg"].notna()]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div style="font-size:9px;font-weight:700;letter-spacing:.1em;color:#22d48a;margin-bottom:6px;">🟢 TOP 10 GAINERS — ALL MARKETS</div>', unsafe_allow_html=True)
            g = valid.nlargest(10,"_chg")[["Flag","Ticker","Company","Price","_chg","Volume"]].copy()
            g.columns = ["","Ticker","Company","Price €","1D %","Volume"]
            g["Price €"] = g["Price €"].apply(lambda x: fv(x,2))
            g["1D %"]    = g["1D %"].apply(fp)
            g["Volume"]  = g["Volume"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
            st.dataframe(g, use_container_width=True, hide_index=True)

        with col2:
            st.markdown('<div style="font-size:9px;font-weight:700;letter-spacing:.1em;color:#e84560;margin-bottom:6px;">🔴 TOP 10 LOSERS — ALL MARKETS</div>', unsafe_allow_html=True)
            l = valid.nsmallest(10,"_chg")[["Flag","Ticker","Company","Price","_chg","Volume"]].copy()
            l.columns = ["","Ticker","Company","Price €","1D %","Volume"]
            l["Price €"] = l["Price €"].apply(lambda x: fv(x,2))
            l["1D %"]    = l["1D %"].apply(fp)
            l["Volume"]  = l["Volume"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
            st.dataframe(l, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── TOP 10 MOMENTUM 12M ──
        st.markdown('<div class="section-hdr">🚀 Top 10 — Best 12-Month Momentum (enriched stocks)</div>', unsafe_allow_html=True)
        mom_valid = enriched[enriched["Mom 12M %"].notna()].nlargest(10, "Mom 12M %")
        if not mom_valid.empty:
            mdf = mom_valid[["Flag","Ticker","Company","Price","1D %","Mom 1W %","Mom 1M %","Mom 6M %","Mom 12M %"]].copy()
            mdf.columns = ["","Ticker","Company","Price €","1D %","1W","1M","6M","12M"]
            mdf["Price €"] = mdf["Price €"].apply(lambda x: fv(x,2))
            for col in ["1D %","1W","1M","6M","12M"]:
                mdf[col] = mdf[col].apply(fp)
            st.dataframe(mdf, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── SECTOR PERFORMANCE ──
        st.markdown('<div class="section-hdr">🏭 Sector Performance — Market Cap Weighted</div>', unsafe_allow_html=True)
        sec_df_raw = enriched.copy()
        sec_df_raw["_mc"]  = pd.to_numeric(sec_df_raw["Market Cap €B"], errors="coerce")
        sec_df_raw["_1d"]  = pd.to_numeric(sec_df_raw["1D %"],          errors="coerce")
        sec_df_raw["_12m"] = pd.to_numeric(sec_df_raw["Mom 12M %"],     errors="coerce")

        sector_rows = []
        for sec, grp in sec_df_raw.groupby("Sector"):
            g1 = grp.dropna(subset=["_mc","_1d"])
            if g1.empty:
                continue
            w = g1["_mc"]; tot = w.sum()
            if tot == 0:
                continue
            wr_1d  = (g1["_1d"] * w).sum() / tot
            g2     = grp.dropna(subset=["_mc","_12m"])
            wr_12m = None
            if not g2.empty:
                w2 = g2["_mc"]; t2 = w2.sum()
                if t2 > 0:
                    wr_12m = (g2["_12m"] * w2).sum() / t2
            sector_rows.append({
                "Sector": sec, "Stocks": len(grp),
                "1D % (MCW)": wr_1d, "12M % (MCW)": wr_12m,
                "Total Mkt Cap €B": tot
            })

        if sector_rows:
            sec_tbl = pd.DataFrame(sector_rows).sort_values("12M % (MCW)", ascending=False, na_position="last")

            fig_sec = px.bar(
                sec_tbl, x="Sector", y="12M % (MCW)",
                color="12M % (MCW)",
                color_continuous_scale=["#e84560","#131720","#22d48a"],
                color_continuous_midpoint=0,
                template="plotly_dark",
                title="12-Month Return by Sector (Market Cap Weighted)"
            )
            fig_sec.update_layout(
                paper_bgcolor="#0d1017", plot_bgcolor="#07090d",
                font_color="#dde4f0", height=320,
                margin=dict(l=0,r=0,t=40,b=0),
                showlegend=False, coloraxis_showscale=False
            )
            st.plotly_chart(fig_sec, use_container_width=True)

            disp_sec = sec_tbl.copy()
            disp_sec["1D % (MCW)"]       = disp_sec["1D % (MCW)"].apply(fp)
            disp_sec["12M % (MCW)"]      = disp_sec["12M % (MCW)"].apply(fp)
            disp_sec["Total Mkt Cap €B"] = disp_sec["Total Mkt Cap €B"].apply(lambda x: fv(x,1))
            st.dataframe(disp_sec, use_container_width=True, hide_index=True)

            st.markdown('<div class="section-hdr">🔍 Sector Drill-Down</div>', unsafe_allow_html=True)
            sec_sel_dd = st.selectbox("Select sector to explore", sorted(sec_df_raw["Sector"].dropna().unique()))
            sec_stocks = sec_df_raw[sec_df_raw["Sector"] == sec_sel_dd].copy()
            if not sec_stocks.empty:
                st.caption(f"**{len(sec_stocks)}** stocks in {sec_sel_dd}")
                dd_cols = ["Flag","Ticker","Company","Country","Price","1D %",
                           "Market Cap €B","Mom 1M %","Mom 12M %","Div Yield %","P/E Fwd 12M"]
                dd = sec_stocks[[c for c in dd_cols if c in sec_stocks.columns]].copy()
                dd["Price"]         = dd["Price"].apply(lambda x: fv(x,2))
                dd["Market Cap €B"] = dd["Market Cap €B"].apply(lambda x: fv(x,1))
                for col in ["1D %","Mom 1M %","Mom 12M %","Div Yield %"]:
                    if col in dd.columns:
                        dd[col] = dd[col].apply(fp)
                if "P/E Fwd 12M" in dd.columns:
                    dd["P/E Fwd 12M"] = dd["P/E Fwd 12M"].apply(lambda x: fv(x,1))
                st.dataframe(dd, use_container_width=True, hide_index=True, height=400)
    else:
        st.warning("No market data available. Press 'Refresh data'.")


# ──────────────────────────────────────────────────────────────────
# EUROZONE SCREEN
# ──────────────────────────────────────────────────────────────────
elif page == "🌍 Eurozone Screen":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0d1017,#131720);border-bottom:1px solid #1e2840;
    padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">
        <span style="font-size:28px;">🌍</span>
        <div>
            <div style="font-size:16px;font-weight:700;color:#dde4f0;">Eurozone — All Markets Screen</div>
            <div style="font-size:10px;color:#5a6880;">All listed European equities · EODHD real data · Value & Growth scored per country</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.warning("⏳ **Loading all stocks for all markets with full enrichment may take 10–20 minutes.** Data is cached for 30 minutes after first load. Subsequent visits are instant.")

    with st.spinner("Loading all Eurozone stocks — enriching ALL stocks per market…"):
        frames_ez = []
        for code in EXCHANGES:
            df_ex = build_exchange_df(code)
            if not df_ex.empty:
                df_ex = enrich_df(df_ex)  # ALL stocks, no limit
                frames_ez.append(df_ex)
        ez_df = pd.concat(frames_ez, ignore_index=True) if frames_ez else pd.DataFrame()

    if not ez_df.empty:
        show_screener(
            ez_df,
            title=f"🌍 Eurozone — {len(ez_df)} stocks across {len(EXCHANGES)} markets",
            exchange_code="EZ"
        )
    else:
        st.error("No Eurozone data available. Check API or refresh.")


# ──────────────────────────────────────────────────────────────────
# SINGLE EXCHANGE SCREENS
# ──────────────────────────────────────────────────────────────────
elif page in PAGE_TO_EXCHANGE:
    exch_code = PAGE_TO_EXCHANGE[page]
    exch_meta = EXCHANGES.get(exch_code, {})
    flag      = exch_meta.get("flag","")
    market    = exch_meta.get("market","")

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0d1017,#131720);border-bottom:1px solid #1e2840;
    padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">
        <span style="font-size:28px;">{flag}</span>
        <div>
            <div style="font-size:16px;font-weight:700;color:#dde4f0;">{market}</div>
            <div style="font-size:10px;color:#5a6880;">Real data EODHD · 15 min delay · All stocks enriched with fundamentals & momentum (may take several minutes)</div>
        </div>
    </div>""", unsafe_allow_html=True)

    if exch_code == "MI":
        st.info("ℹ️ **Technical note:** EODHD does not carry Borsa Italiana as a direct exchange. Italian stocks are extracted from XETRA by filtering for Italian ISINs (IT*). EUR prices are aligned with Milan exchange.")

    with st.spinner(f"Loading {market} stocks…"):
        df_exch = build_exchange_df(exch_code)

    if df_exch.empty:
        st.error(f"No data for {market}. Check API or press 'Refresh data'.")
    else:
        with st.spinner(f"Enriching all {len(df_exch)} stocks with fundamentals & momentum — this may take several minutes…"):
            df_exch = enrich_df(df_exch)  # ALL stocks, no limit

        show_screener(
            df_exch,
            title=f"{flag} {market} — {len(df_exch)} stocks",
            exchange_code=exch_code
        )


# ──────────────────────────────────────────────────────────────────
# PORTFOLIOS
# ──────────────────────────────────────────────────────────────────
elif page == "💼 Portfolios":
    st.markdown('<div class="section-hdr">💼 Portfolio Management</div>', unsafe_allow_html=True)

    if "portfolios" not in st.session_state:
        st.session_state.portfolios = {
            "Portfolio 1": {}, "Portfolio 2": {}, "Portfolio 3": {}
        }

    pf_names = list(st.session_state.portfolios.keys())
    c_sel, c_new = st.columns([3,2])
    with c_sel:
        active_pf = st.selectbox("Active portfolio", pf_names)
    with c_new:
        new_pf_name = st.text_input("New portfolio name", placeholder="e.g. Growth EU")
        if st.button("+ Create") and new_pf_name and len(st.session_state.portfolios) < 10:
            st.session_state.portfolios[new_pf_name] = {}
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-hdr">➕ Add stock manually</div>', unsafe_allow_html=True)
    st.caption("For Italian stocks use XETRA ticker: **ENI.XETRA**, **ENEL.XETRA**, **ISP.XETRA**, **STM.XETRA**")

    a1,a2,a3,a4 = st.columns([3,1,1,1])
    with a1:
        ticker_input = st.text_input("EODHD Ticker", placeholder="e.g. ENI.XETRA, SAP.XETRA, ASML.AS")
    with a2:
        qty_input  = st.number_input("Quantity", min_value=0.0, step=1.0)
    with a3:
        cost_input = st.number_input("Buy price €", min_value=0.0, step=0.01)
    with a4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("+ Add"):
            if qty_input > 0 and cost_input > 0 and ticker_input:
                pf = st.session_state.portfolios[active_pf]
                if len(pf) >= 50:
                    st.error("Max 50 stocks per portfolio")
                else:
                    pf[ticker_input] = {"qty": qty_input, "cost": cost_input}
                    st.success(f"Added {ticker_input}")
                    st.rerun()

    pf_data = st.session_state.portfolios.get(active_pf, {})
    if not pf_data:
        st.info("No stocks yet. Add stocks above or from any screen page.")
    else:
        with st.spinner("Loading portfolio prices…"):
            rows = []
            total_cost = total_curr = total_1d = 0

            for full_ticker, h in pf_data.items():
                q = eodhd_get(f"real-time/{full_ticker}")
                if isinstance(q, list):
                    q = q[0] if q else {}
                if not q:
                    q = {}
                px    = q.get("close") or q.get("adjusted_close") or h["cost"]
                chg_p = q.get("change_p", 0)
                try:   chg_p = float(chg_p) if chg_p is not None else 0.0
                except: chg_p = 0.0
                try:   px = float(px)
                except: px = float(h["cost"])

                qty      = h["qty"]
                cost_px  = h["cost"]
                cost_val = qty * cost_px
                curr_val = qty * px
                pnl      = curr_val - cost_val
                pnl_pct  = pnl / cost_val * 100 if cost_val else 0
                pnl_1d   = curr_val * chg_p / 100

                total_cost += cost_val
                total_curr += curr_val
                total_1d   += pnl_1d

                rows.append({
                    "Ticker": full_ticker, "Qty": qty,
                    "Buy Price €": cost_px, "Cost Value €": cost_val,
                    "Current Price €": px,  "Market Value €": curr_val,
                    "Weight %": None,
                    "P&L €": pnl, "P&L %": pnl_pct, "P&L Today €": pnl_1d,
                })

            for r in rows:
                r["Weight %"] = r["Market Value €"] / total_curr * 100 if total_curr else 0

        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Invested",      f"€ {total_cost:,.0f}")
        k2.metric("Market Value",  f"€ {total_curr:,.0f}",
                  fp((total_curr-total_cost)/total_cost*100) if total_cost else "—")
        k3.metric("Total P&L",     f"€ {total_curr-total_cost:+,.0f}",
                  fp((total_curr-total_cost)/total_cost*100) if total_cost else "—")
        k4.metric("P&L Today",     f"€ {total_1d:+,.0f}")

        st.markdown("---")
        pf_df = pd.DataFrame(rows)

        ch1, ch2 = st.columns(2)
        with ch1:
            exch_d = pf_df.groupby(
                pf_df["Ticker"].str.split(".").str[-1]
            )["Market Value €"].sum().reset_index()
            exch_d.columns = ["Exchange","Value €"]
            fig = px.pie(exch_d, values="Value €", names="Exchange",
                         title="By Exchange", template="plotly_dark",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(paper_bgcolor="#0d1017", plot_bgcolor="#0d1017",
                              font_color="#dde4f0", height=260,
                              margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            fig2 = px.bar(pf_df.sort_values("P&L %", ascending=False),
                          x="Ticker", y="P&L %",
                          color="P&L %",
                          color_continuous_scale=["#e84560","#131720","#22d48a"],
                          color_continuous_midpoint=0,
                          title="P&L % per stock", template="plotly_dark")
            fig2.update_layout(paper_bgcolor="#0d1017", plot_bgcolor="#0d1017",
                               font_color="#dde4f0", height=260,
                               margin=dict(l=0,r=0,t=30,b=40),
                               showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

        disp = pf_df.copy()
        for c in ["Buy Price €","Current Price €"]:
            disp[c] = disp[c].apply(lambda x: fv(x,2))
        for c in ["Cost Value €","Market Value €","P&L €","P&L Today €"]:
            disp[c] = disp[c].apply(lambda x: f"€ {x:+,.0f}" if pd.notna(x) else "—")
        for c in ["Weight %","P&L %"]:
            disp[c] = disp[c].apply(lambda x: fp(x,1))
        disp["Qty"] = disp["Qty"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(disp, use_container_width=True, hide_index=True)

        rm_sel = st.selectbox("Remove stock", list(pf_data.keys()))
        if st.button("🗑️ Remove"):
            del st.session_state.portfolios[active_pf][rm_sel]
            st.rerun()


# ──────────────────────────────────────────────────────────────────
# INFO & DATA
# ──────────────────────────────────────────────────────────────────
elif page == "ℹ️ Info & Data":
    st.markdown('<div class="section-hdr">ℹ️ EuroEquity Pro — Info & Data Sources</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Analyst:** Andrea Meschini, CFA Charterholder Level III  
**University:** Ca' Foscari, Venice  
**Experience:**
- JP Morgan London — Asst. Portfolio Manager (4 years)
- Zenith SGR — Equity Fund Manager, pension fund (5 years)

**Address:** Via Lorenzo Fava 24, 37139 Verona  
**Tel/WhatsApp:** +39 351 837 3385  
**Email:** andreameschini19@gmail.com
        """)
    with col2:
        st.markdown("""
**Legal disclaimer:** Data and tools provided are for informational purposes only and do not constitute personalized investment advice under MiFID II or D.Lgs. 58/1998 (TUF). Andrea Meschini — Independent Financial Advisor, OCF Register.

**Borsa Italiana:** EODHD does not carry Borsa Italiana as a direct exchange. Italian stocks are extracted from XETRA by filtering for Italian ISINs (IT*). EUR prices are aligned with Milan exchange.

**Value Score (1–100):** Ranked per country. Inputs: Earnings Yield trailing (1/PE), Earnings Yield forward (1/PE fwd), inverse P/B. Each input ranked 1–100 → sum → re-ranked 1–100.

**Growth Score (1–100):** Ranked per country. Inputs: EPS growth %, Revenue growth %, EPS momentum (fwd vs trailing EPS), 12M minus 1M momentum, 6M minus 1W momentum. Each ranked 1–100 → sum → re-ranked 1–100.
        """)

    st.markdown("---")
    st.markdown('<div class="section-hdr">📡 Data Sources & Costs</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        ["Bulk EOD prices (all exchanges)",      "EODHD Bulk EOD",       "$20/mo", "1 API call per exchange"],
        ["Italian stocks via XETRA (ISIN IT*)",  "EODHD Bulk EOD XETRA", "$20/mo", "ENI, Enel, Intesa, STM…"],
        ["Fundamentals (PE, PB, Beta, ROE…)",    "EODHD Fundamentals",   "$20/mo", "Updated end of day"],
        ["Momentum (price history 1W/1M/6M/12M)","EODHD Historical EOD", "$20/mo", "Up to 30 years daily"],
        ["Index performance (13 indices)",       "EODHD Real-time",      "$20/mo", "FTSE MIB, DAX, CAC…"],
        ["Hosting",                              "Streamlit Cloud",      "Free",   ""],
        ["TOTAL",                                "",                     "$20/mo", "EODHD All-World plan"],
    ], columns=["Data","Provider","Cost","Notes"]), use_container_width=True, hide_index=True)
