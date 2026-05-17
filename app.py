"""
EuroEquity Pro — BETA
AManalysis LTD · Andrea Meschini, CFA
Beta version: all features free, no paywall, no Stripe
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

from legal import FOOTER_HTML, COOKIE_BANNER_HTML, TERMS_OF_USE, PRIVACY_POLICY, COOKIE_POLICY, DISCLAIMER

st.set_page_config(
    page_title="EuroEquity Pro — Beta",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

EODHD_KEY  = "6a0826ce2e8a52.04646471"
EODHD_BASE = "https://eodhd.com/api"
ITALIAN_ISIN_PREFIX = "IT"
MAX_SCREEN  = 100

ALL_COLS = ["Ticker","Company","Sector","Country","Price","1D %",
            "Market Cap €B","P/E Trail.","P/E Fwd 12M","P/B","EV/EBITDA",
            "ROE %","Div Yield %","Beta",
            "EPS Gr %","Rev Gr %","EPS Mom 30d",
            "Mom 1W %","Mom 1M %","Mom 6M %","Mom 12M %",
            "Value Score","Growth Score"]

# ── CSS ──────────────────────────────────────────────────────────
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

# ── CONSTANTS ────────────────────────────────────────────────────
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

# ── API ──────────────────────────────────────────────────────────
def eodhd_get(endpoint, params=None):
    if params is None: params = {}
    params["api_token"] = EODHD_KEY
    params["fmt"] = "json"
    try:
        r = requests.get(f"{EODHD_BASE}/{endpoint}", params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_exchange_tickers(exchange_code):
    data = eodhd_get(f"exchange-symbol-list/{exchange_code}", {"type":"common_stock"})
    return data or []

@st.cache_data(ttl=3600, show_spinner=False)
def get_bulk_eod(exchange_code):
    data = eodhd_get(f"eod-bulk-last-day/{exchange_code}")
    if not data: return pd.DataFrame()
    return pd.DataFrame(data)

@st.cache_data(ttl=3600, show_spinner=False)
def get_italian_stocks_from_xetra():
    bulk    = get_bulk_eod("XETRA")
    tickers = get_exchange_tickers("XETRA")
    if bulk.empty or not tickers: return pd.DataFrame(), {}
    ticker_info   = {t.get("Code",""): t for t in tickers}
    italian_codes = {t.get("Code","") for t in tickers
                     if (t.get("ISIN") or "").startswith(ITALIAN_ISIN_PREFIX)}
    if "code" not in bulk.columns or not italian_codes:
        return pd.DataFrame(), ticker_info
    return bulk[bulk["code"].isin(italian_codes)].copy(), ticker_info

@st.cache_data(ttl=7200, show_spinner=False)
def get_fundamentals(ticker_exchange):
    data = eodhd_get(f"fundamentals/{ticker_exchange}")
    if not data: return {}
    h = data.get("Highlights", {}) or {}
    v = data.get("Valuation",   {}) or {}
    t = data.get("Technicals",  {}) or {}
    g = data.get("General",     {}) or {}

    def sm(val,m):
        try: return float(val)*m if val is not None else None
        except: return None
    def sd(val,d):
        try: return float(val)/d if val is not None and d else None
        except: return None

    # EPS Momentum 30d from Earnings Trend
    eps_mom = None
    recent_earnings = False
    try:
        earnings = data.get("Earnings", {}) or {}
        trend    = earnings.get("Trend", {}) or {}
        history  = earnings.get("History", {}) or {}
        today    = datetime.utcnow().date()
        for date_str, rec in history.items():
            try:
                rep_date = datetime.strptime(date_str[:10],"%Y-%m-%d").date()
                if abs((today-rep_date).days) <= 5 and rec.get("epsActual") is not None:
                    recent_earnings = True
                    break
            except: pass
        if trend:
            dates = sorted(trend.keys(), reverse=True)
            if dates:
                latest  = trend[dates[0]]
                eps_now = latest.get("epsTrendCurrent")
                eps_30d = latest.get("epsTrend30daysAgo")
                if eps_now is not None and eps_30d is not None:
                    en  = float(eps_now)
                    e30 = float(eps_30d)
                    if e30 != 0:
                        eps_mom = (en - e30) / abs(e30) * 100
    except: pass

    sector = (g.get("Sector") or g.get("GicSector") or "").strip() or None

    return {
        "sector":          sector,
        "pe_t":            h.get("PERatio"),
        "pe_f":            h.get("ForwardPE"),
        "pb":              v.get("PriceBookMRQ"),
        "ev_ebitda":       v.get("EnterpriseValueEbitda"),
        "mktcap":          sd(h.get("MarketCapitalization"), 1e9),
        "roe":             sm(h.get("ReturnOnEquityTTM"), 100),
        "div_yield":       sm(h.get("DividendYield"), 100),
        "beta":            t.get("Beta"),
        "earnings_growth": sm(h.get("QuarterlyEarningsGrowthYOY"), 100),
        "revenue_growth":  sm(h.get("QuarterlyRevenueGrowthYOY"), 100),
        "eps_mom_30d":     eps_mom,
        "recent_earnings": recent_earnings,
    }

@st.cache_data(ttl=3600, show_spinner=False)
def get_price_history(ticker_exchange, period_days=400):
    from_date = (datetime.now()-timedelta(days=period_days)).strftime("%Y-%m-%d")
    data = eodhd_get(f"eod/{ticker_exchange}", {"from":from_date,"period":"d"})
    if not data: return None
    df = pd.DataFrame(data)
    if df.empty: return None
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")

@st.cache_data(ttl=900, show_spinner=False)
def get_index_quote(index_ticker):
    data = eodhd_get(f"real-time/{index_ticker}", {"s":index_ticker})
    if data:
        d = data[0] if isinstance(data,list) else data
        if d.get("close") or d.get("adjusted_close"): return d
    eod = eodhd_get(f"eod/{index_ticker}", {"period":"d"})
    if eod and isinstance(eod,list) and len(eod)>=2:
        last=eod[-1]; prev=eod[-2]
        close  = float(last.get("adjusted_close") or last.get("close") or 0)
        prev_c = float(prev.get("adjusted_close") or prev.get("close") or 1)
        chg_p  = (close/prev_c-1)*100 if prev_c else 0
        return {"close":close,"change_p":chg_p,"timestamp":None}
    return None

# ── BUILD PRICE DATAFRAME ─────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def build_exchange_df(exchange_code):
    exch_meta = EXCHANGES.get(exchange_code,{})
    flag      = exch_meta.get("flag","")
    if exchange_code == "MI":
        bulk, ticker_info = get_italian_stocks_from_xetra()
        source_exch = "XETRA"
        if bulk.empty: return pd.DataFrame()
    else:
        bulk        = get_bulk_eod(exchange_code)
        tickers     = get_exchange_tickers(exchange_code)
        ticker_info = {t.get("Code",""): t for t in tickers}
        source_exch = exchange_code
    if bulk.empty or "code" not in bulk.columns: return pd.DataFrame()
    rows = []
    for _, row in bulk.iterrows():
        code  = row.get("code","")
        if not code: continue
        info  = ticker_info.get(code,{})
        itype = info.get("Type","")
        if itype in ["ETF","Fund","FUND","Preferred Stock"]: continue
        chg = row.get("change_p")
        try:    chg = float(chg) if chg is not None else None
        except: chg = None
        name = info.get("Name", code)
        rows.append({
            "EODHD_Ticker":   f"{code}.{source_exch}",
            "Ticker":         code,
            "Company":        name,
            "Country":        exch_meta.get("label",""),
            "Flag":           flag,
            "Exchange":       exchange_code,
            "Sector":         None,
            "Price":          row.get("close") or row.get("adjusted_close"),
            "1D %":           chg,
            "Volume":         row.get("volume"),
            "Market Cap €B":  None,"P/E Trail.":None,"P/E Fwd 12M":None,
            "P/B":None,"EV/EBITDA":None,"ROE %":None,"Div Yield %":None,"Beta":None,
            "EPS Gr %":None,"Rev Gr %":None,"EPS Mom 30d":None,"Recent Earnings":False,
            "Mom 1W %":None,"Mom 1M %":None,"Mom 6M %":None,"Mom 12M %":None,
            "Value Score":None,"Growth Score":None,
        })
    return pd.DataFrame(rows)

# ── ENRICH ───────────────────────────────────────────────────────
def enrich_rows(df, indices, show_progress=True):
    if df.empty or len(indices)==0: return df
    df    = df.copy()
    total = len(indices)
    prog  = st.progress(0,"Loading fundamentals & momentum…") if show_progress else None

    for i, idx in enumerate(indices):
        tk = df.at[idx,"EODHD_Ticker"]
        try:
            f = get_fundamentals(tk)
            if f:
                if f.get("sector"):     df.at[idx,"Sector"]         = f["sector"]
                df.at[idx,"Market Cap €B"]  = f.get("mktcap")
                df.at[idx,"P/E Trail."]     = f.get("pe_t")
                df.at[idx,"P/E Fwd 12M"]    = f.get("pe_f")
                df.at[idx,"P/B"]            = f.get("pb")
                df.at[idx,"EV/EBITDA"]      = f.get("ev_ebitda")
                df.at[idx,"ROE %"]          = f.get("roe")
                df.at[idx,"Div Yield %"]    = f.get("div_yield")
                df.at[idx,"Beta"]           = f.get("beta")
                df.at[idx,"EPS Gr %"]       = f.get("earnings_growth")
                df.at[idx,"Rev Gr %"]       = f.get("revenue_growth")
                df.at[idx,"EPS Mom 30d"]    = f.get("eps_mom_30d")
                df.at[idx,"Recent Earnings"]= f.get("recent_earnings", False)
        except: pass
        try:
            hist = get_price_history(tk, 400)
            if hist is not None and len(hist)>=5:
                closes = hist["adjusted_close"].dropna().values
                n=len(closes); last=closes[-1]
                if n>=5:   df.at[idx,"Mom 1W %"]  = (last/closes[max(0,n-5)]  -1)*100
                if n>=21:  df.at[idx,"Mom 1M %"]  = (last/closes[max(0,n-21)] -1)*100
                if n>=126: df.at[idx,"Mom 6M %"]  = (last/closes[max(0,n-126)]-1)*100
                if n>=252: df.at[idx,"Mom 12M %"] = (last/closes[max(0,n-252)]-1)*100
        except: pass
        if prog: prog.progress((i+1)/total, text=f"Enriching {i+1}/{total}: {df.at[idx,'Ticker']}")

    if prog: prog.empty()

    def rank100(s): return s.rank(pct=True,na_option="keep")*100
    def safe_inv(col):
        return col.apply(lambda x: 1/float(x) if x is not None and str(x) not in ["","nan"] and float(str(x) or 0)>0 else None)

    sub   = df.loc[indices]
    r_eyt = rank100(safe_inv(sub["P/E Trail."]))
    r_eyf = rank100(safe_inv(sub["P/E Fwd 12M"]))
    r_pb  = rank100(safe_inv(sub["P/B"]))
    df.loc[indices,"Value Score"] = rank100(r_eyt.add(r_eyf,fill_value=0).add(r_pb,fill_value=0)).round(0)

    m12=pd.to_numeric(sub["Mom 12M %"],errors="coerce")
    m1 =pd.to_numeric(sub["Mom 1M %"], errors="coerce")
    m6 =pd.to_numeric(sub["Mom 6M %"], errors="coerce")
    m1w=pd.to_numeric(sub["Mom 1W %"], errors="coerce")
    df.loc[indices,"Growth Score"] = rank100(
        rank100(pd.to_numeric(sub["EPS Gr %"],   errors="coerce"))
        .add(rank100(pd.to_numeric(sub["Rev Gr %"],   errors="coerce")),fill_value=0)
        .add(rank100(pd.to_numeric(sub["EPS Mom 30d"],errors="coerce")),fill_value=0)
        .add(rank100(m12-m1),fill_value=0)
        .add(rank100(m6-m1w), fill_value=0)
    ).round(0)
    return df

# ── DASHBOARD UNIVERSE ────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _load_all_prices():
    frames = []
    for code in EXCHANGES:
        df_ex = build_exchange_df(code)
        if not df_ex.empty:
            frames.append(df_ex)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_dashboard_universe():
    """
    Dashboard universe built from BULK EOD only — zero fundamental API calls.
    Fast: 11 bulk calls (one per exchange), all cached.
    Top movers, momentum proxy (1D%), and sector breakdown from prices only.
    """
    frames=[]
    for code in EXCHANGES:
        df_ex = build_exchange_df(code)
        if not df_ex.empty: frames.append(df_ex)
    if not frames: return pd.DataFrame()
    all_p = pd.concat(frames, ignore_index=True)
    all_p["_vol"] = pd.to_numeric(all_p["Volume"], errors="coerce")
    all_p["_chg"] = pd.to_numeric(all_p["1D %"],   errors="coerce")
    all_p["_px"]  = pd.to_numeric(all_p["Price"],   errors="coerce")
    return all_p

# ── FORMATTING ───────────────────────────────────────────────────
def fp(v,d=1):
    if v is None: return "—"
    try:
        v=float(v)
        if np.isnan(v): return "—"
    except: return "—"
    return f"{'+'if v>=0 else ''}{v:.{d}f}%"

def fv(v,d=2):
    if v is None: return "—"
    try:
        v=float(v)
        if np.isnan(v): return "—"
    except: return "—"
    return f"{v:.{d}f}"

def fn(v):
    if v is None: return "—"
    try:
        v=float(v)
        if np.isnan(v): return "—"
        return str(int(v))
    except: return "—"

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="color:#c8982a;font-weight:700;font-size:15px;margin-bottom:2px;font-style:italic;">📊 EuroEquity Pro</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:9px;color:#22d48a;margin-bottom:4px;font-weight:700;">🧪 BETA — Free Access</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:9px;color:#5a6880;margin-bottom:16px;">Andrea Meschini, CFA · AManalysis LTD</div>', unsafe_allow_html=True)

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
        "📋 Legal",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div style="font-size:9px;color:#5a6880;line-height:1.6;"><b style="color:#22d48a;">● LIVE DATA</b> · EODHD<br>Prices: 15 min delay<br>Fundamentals: on demand<br>Cache: 2h</div>', unsafe_allow_html=True)
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

# Beta banner
st.markdown("""
<div style="background:rgba(200,152,42,0.08);border:1px solid rgba(200,152,42,0.25);
padding:8px 16px;margin-bottom:12px;border-radius:3px;font-size:11px;color:#c8982a;">
🧪 <b>BETA VERSION</b> — All features are free during the beta period.
Data is for informational purposes only · Not investment advice · Prices delayed 15 min
</div>
""", unsafe_allow_html=True)

# ── SCREENER ─────────────────────────────────────────────────────
def show_screener(df, title="", exchange_code=""):
    if df.empty:
        if exchange_code=="MI":
            st.error("Italian stocks (XETRA ISIN IT*) not loaded. Press **🔄 Refresh data** in the sidebar.")
        else:
            st.error("No data. Press **🔄 Refresh data**.")
        return

    if exchange_code=="MI":
        st.info(f"🇮🇹 Italian stocks extracted from XETRA by ISIN IT* · {len(df)} stocks found")

    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)
    st.markdown("### ⚙️ Set filters — then click **Load & Apply**")
    st.caption(f"Total available: **{len(df)}** stocks · Max enriched per load: **{MAX_SCREEN}** · All parameters visible in beta")

    f1,f2,f3,f4 = st.columns(4)
    with f1:
        st.markdown("**Price & Volume**")
        price_min = st.number_input("Price min €",     0.0, step=0.5,  key=f"px_{title[:8]}")
        price_max = st.number_input("Price max €",     0.0, step=1.0,  key=f"pxm_{title[:8]}")
        vol_min   = st.number_input("Volume min (k)",  0.0, step=10.0, key=f"vol_{title[:8]}")
    with f2:
        st.markdown("**Performance**")
        chg_min   = st.number_input("1D % min",       -50.0,step=0.5,  key=f"cmin_{title[:8]}")
        chg_max   = st.number_input("1D % max",        50.0,step=0.5,  key=f"cmax_{title[:8]}")
        mom12_min = st.number_input("Mom 12M % min",   0.0, step=5.0,  key=f"m12_{title[:8]}")
    with f3:
        st.markdown("**Fundamentals**")
        pe_f_max  = st.number_input("P/E Fwd max",    0.0, step=1.0,  key=f"pe_{title[:8]}")
        pb_max    = st.number_input("P/B max",         0.0, step=0.5,  key=f"pb_{title[:8]}")
        div_min   = st.number_input("Div Yield % min", 0.0, step=0.5,  key=f"dv_{title[:8]}")
        roe_min   = st.number_input("ROE % min",       0.0, step=1.0,  key=f"roe_{title[:8]}")
        beta_max  = st.number_input("Beta max",        0.0, step=0.1,  key=f"bt_{title[:8]}")
    with f4:
        st.markdown("**Scores & Sort**")
        val_min   = st.number_input("Value Score min", 0.0, step=5.0,  key=f"vs_{title[:8]}")
        grow_min  = st.number_input("Growth Score min",0.0, step=5.0,  key=f"gs_{title[:8]}")
        sort_col  = st.selectbox("Sort by",[
            "Market Cap €B","Volume","1D %","Mom 12M %","Mom 6M %","Mom 1M %","Mom 1W %",
            "P/E Fwd 12M","Div Yield %","ROE %","Beta","Value Score","Growth Score","Price"
        ], key=f"srt_{title[:8]}")
        sort_asc  = st.checkbox("Ascending", False, key=f"asc_{title[:8]}")
        search    = st.text_input("Search ticker / name","", key=f"srch_{title[:8]}")

    # Price filters (instant)
    fdf = df.copy()
    fdf["_chg"]=pd.to_numeric(fdf["1D %"],errors="coerce")
    fdf["_vol"]=pd.to_numeric(fdf["Volume"],errors="coerce")
    fdf["_px"] =pd.to_numeric(fdf["Price"], errors="coerce")
    if search:
        q=search.lower()
        fdf=fdf[fdf["Ticker"].str.lower().str.contains(q,na=False)|fdf["Company"].str.lower().str.contains(q,na=False)]
    if price_min>0: fdf=fdf[fdf["_px"]>=price_min]
    if price_max>0: fdf=fdf[fdf["_px"]<=price_max]
    if vol_min>0:   fdf=fdf[fdf["_vol"]>=vol_min*1000]
    if chg_min!=0:  fdf=fdf[fdf["_chg"]>=chg_min]
    if chg_max!=50: fdf=fdf[fdf["_chg"]<=chg_max]
    fdf=fdf.sort_values("_vol",ascending=False,na_position="last")
    candidates=fdf.head(MAX_SCREEN)

    st.info(f"**{len(fdf)}** stocks match price/volume filters · Will enrich top **{len(candidates)}** by volume")

    state_key=f"enriched_{exchange_code}_{title[:8]}"
    if state_key not in st.session_state: st.session_state[state_key]=None

    if st.button(f"⚡ Load & Apply — enrich {len(candidates)} stocks",
                 key=f"btn_{title[:8]}", type="primary"):
        enriched_df = enrich_rows(df, candidates.index.tolist())
        st.session_state[state_key] = enriched_df

    if st.session_state[state_key] is None:
        st.markdown("---")
        st.markdown("👆 **Set filters above and click Load & Apply to see results.**")
        return

    # Fundamental filters
    edf=st.session_state[state_key].loc[candidates.index].copy()
    edf["_mc_n"] =pd.to_numeric(edf["Market Cap €B"],errors="coerce")
    edf["_pe_n"] =pd.to_numeric(edf["P/E Fwd 12M"],  errors="coerce")
    edf["_pb_n"] =pd.to_numeric(edf["P/B"],           errors="coerce")
    edf["_dv_n"] =pd.to_numeric(edf["Div Yield %"],   errors="coerce")
    edf["_roe_n"]=pd.to_numeric(edf["ROE %"],         errors="coerce")
    edf["_bt_n"] =pd.to_numeric(edf["Beta"],          errors="coerce")
    edf["_m12_n"]=pd.to_numeric(edf["Mom 12M %"],     errors="coerce")
    edf["_vs_n"] =pd.to_numeric(edf["Value Score"],   errors="coerce")
    edf["_gs_n"] =pd.to_numeric(edf["Growth Score"],  errors="coerce")

    if pe_f_max>0: edf=edf[edf["_pe_n"].isna()|(edf["_pe_n"]<=pe_f_max)]
    if pb_max>0:   edf=edf[edf["_pb_n"].isna()|(edf["_pb_n"]<=pb_max)]
    if div_min>0:  edf=edf[edf["_dv_n"]>=div_min]
    if roe_min>0:  edf=edf[edf["_roe_n"]>=roe_min]
    if beta_max>0: edf=edf[edf["_bt_n"].isna()|(edf["_bt_n"]<=beta_max)]
    if mom12_min>0:edf=edf[edf["_m12_n"]>=mom12_min]
    if val_min>0:  edf=edf[edf["_vs_n"]>=val_min]
    if grow_min>0: edf=edf[edf["_gs_n"]>=grow_min]

    sort_map={"Market Cap €B":"_mc_n","1D %":"_chg","Volume":"_vol","Price":"_px",
              "Mom 12M %":"_m12_n","P/E Fwd 12M":"_pe_n","Div Yield %":"_dv_n",
              "ROE %":"_roe_n","Beta":"_bt_n","Value Score":"_vs_n","Growth Score":"_gs_n"}
    sc=sort_map.get(sort_col,sort_col)
    if sc in edf.columns: edf=edf.sort_values(sc,ascending=sort_asc,na_position="last")

    st.success(f"✅ **{len(edf)}** stocks after all filters")

    # Display table
    show_cols=[c for c in ALL_COLS if c in edf.columns]
    ddf=edf[show_cols].copy()
    ddf["Sector"]=ddf["Sector"].fillna("—")
    for col in ["Price","Market Cap €B","P/E Trail.","P/E Fwd 12M","P/B","EV/EBITDA","Beta"]:
        if col in ddf.columns:
            ddf[col]=ddf[col].apply(lambda x:fv(x,2 if col in ["Price","P/B","Beta"] else 1))
    for col in ["ROE %","Div Yield %","EPS Gr %","Rev Gr %","EPS Mom 30d",
                "1D %","Mom 1W %","Mom 1M %","Mom 6M %","Mom 12M %"]:
        if col in ddf.columns: ddf[col]=ddf[col].apply(fp)
    for col in ["Value Score","Growth Score"]:
        if col in ddf.columns: ddf[col]=ddf[col].apply(fn)

    if "Recent Earnings" in edf.columns:
        ddf.insert(2,"📅",edf["Recent Earnings"].apply(lambda x:"📅" if x else ""))

    st.dataframe(ddf, use_container_width=True, hide_index=True, height=480,
        column_config={
            "Ticker":       st.column_config.TextColumn("Ticker",  width=70),
            "Company":      st.column_config.TextColumn("Company", width=170),
            "Sector":       st.column_config.TextColumn("Sector",  width=120),
            "📅":           st.column_config.TextColumn("📅",      width=30),
            "Value Score":  st.column_config.TextColumn("Value",   width=52),
            "Growth Score": st.column_config.TextColumn("Growth",  width=58),
        })
    st.caption("📅 = Earnings reported within last 5 days — forward EPS may be rolling to new fiscal year")

    # Stock detail
    if edf.empty: return
    st.markdown("---")
    st.markdown('<div class="section-hdr">📈 Stock Detail</div>', unsafe_allow_html=True)
    sel_ticker=st.selectbox("Select stock",edf["Ticker"].tolist(),
        format_func=lambda t: f"{t}  —  {edf[edf['Ticker']==t]['Company'].values[0] if not edf[edf['Ticker']==t].empty else t}",
        key=f"det_{title[:8]}")
    sel_row=edf[edf["Ticker"]==sel_ticker]
    if sel_row.empty: return
    r=sel_row.iloc[0]
    eodhd_tk=r["EODHD_Ticker"]
    if r.get("Recent Earnings"):
        st.warning("📅 Earnings reported within last 5 days — forward EPS estimates may have rolled to new fiscal year.")

    c1,c2,c3,c4,c5,c6,c7,c8=st.columns(8)
    c1.metric("Price €",      fv(r.get("Price"),2))
    c2.metric("1D %",         fp(r.get("1D %")))
    c3.metric("Mkt Cap €B",   fv(r.get("Market Cap €B"),1))
    c4.metric("P/E Trailing", fv(r.get("P/E Trail."),1))
    c5.metric("P/E Fwd 12M",  fv(r.get("P/E Fwd 12M"),1))
    c6.metric("P/B",          fv(r.get("P/B"),2))
    c7.metric("EV/EBITDA",    fv(r.get("EV/EBITDA"),1))
    c8.metric("Beta",         fv(r.get("Beta"),2))

    d1,d2,d3,d4,d5,d6,d7,d8=st.columns(8)
    d1.metric("ROE %",        fp(r.get("ROE %")))
    d2.metric("Div Yield %",  fp(r.get("Div Yield %")))
    d3.metric("EPS Gr %",     fp(r.get("EPS Gr %")))
    d4.metric("Rev Gr %",     fp(r.get("Rev Gr %")))
    d5.metric("EPS Mom 30d",  fp(r.get("EPS Mom 30d")))
    d6.metric("Mom 1M",       fp(r.get("Mom 1M %")))
    d7.metric("Mom 12M",      fp(r.get("Mom 12M %")))
    d8.metric("Value/Growth", f"{fn(r.get('Value Score'))} / {fn(r.get('Growth Score'))}")

    e1,e2,e3,e4=st.columns(4)
    e1.metric("Mom 1W",  fp(r.get("Mom 1W %")))
    e2.metric("Mom 6M",  fp(r.get("Mom 6M %")))
    e3.metric("Sector",  r.get("Sector") or "—")
    e4.metric("Country", r.get("Country") or "—")

    period_map={"1Y":365,"3Y":3*365,"5Y":5*365}
    period_sel=st.radio("Chart period",list(period_map.keys()),horizontal=True,key=f"cp_{title[:8]}")
    with st.spinner("Loading chart…"):
        hist=get_price_history(eodhd_tk,period_map[period_sel])
    if hist is not None and not hist.empty:
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=hist["date"],y=hist["adjusted_close"],
            mode="lines",name=sel_ticker,line=dict(color="#c8982a",width=2)))
        fig.update_layout(title=f"{r['Company']} ({sel_ticker}) — {period_sel}",
            xaxis_title="",yaxis_title="Price (EUR)",template="plotly_dark",
            paper_bgcolor="#0d1017",plot_bgcolor="#07090d",font_color="#dde4f0",
            height=360,margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("Price history not available.")

    st.markdown("---")
    st.markdown('<div class="section-hdr">➕ Add to portfolio</div>', unsafe_allow_html=True)
    if "portfolios" not in st.session_state:
        st.session_state.portfolios={"Portfolio 1":{},"Portfolio 2":{},"Portfolio 3":{}}
    pa1,pa2,pa3,pa4=st.columns([2,1,1,1])
    with pa1: pf_target=st.selectbox("Portfolio",list(st.session_state.portfolios.keys()),key=f"pf_{title[:8]}_{sel_ticker}")
    with pa2: qty_add=st.number_input("Qty",min_value=0.0,step=1.0,key=f"qty_{title[:8]}_{sel_ticker}")
    with pa3: cost_add=st.number_input("Buy price €",min_value=0.0,step=0.01,value=float(r.get("Price") or 0),key=f"cost_{title[:8]}_{sel_ticker}")
    with pa4:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("➕ Add",key=f"addpf_{title[:8]}_{sel_ticker}"):
            if qty_add>0 and cost_add>0:
                pf=st.session_state.portfolios[pf_target]
                if len(pf)<50:
                    pf[eodhd_tk]={"qty":qty_add,"cost":cost_add}
                    st.success(f"Added {eodhd_tk} to {pf_target}")
                else: st.error("Max 50 stocks per portfolio")

# ── DASHBOARD ────────────────────────────────────────────────────
if page=="🏠 Dashboard":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0d1017,#131720);border-bottom:1px solid #1e2840;
    padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
        <span style="font-size:22px;font-weight:700;color:#c8982a;font-style:italic;">EuroEquity
        <span style="color:#dde4f0;">Pro</span></span>
        <span style="font-size:9px;background:rgba(200,152,42,0.15);color:#c8982a;
        border:1px solid rgba(200,152,42,0.4);padding:2px 8px;border-radius:2px;font-weight:700;">🧪 BETA</span>
        <span style="font-size:9px;background:rgba(34,212,138,0.1);color:#22d48a;
        border:1px solid rgba(34,212,138,0.3);padding:2px 8px;border-radius:2px;
        letter-spacing:.1em;font-weight:700;">● LIVE DATA · EODHD</span>
        <span style="font-size:9px;background:rgba(90,104,128,0.2);color:#8a9ab8;
        border:1px solid rgba(90,104,128,0.3);padding:2px 8px;border-radius:2px;">15 MIN DELAY</span>
        <span style="font-size:10px;color:#5a6880;margin-left:auto;">Andrea Meschini, CFA · AManalysis LTD</span>
    </div>""",unsafe_allow_html=True)

    dash_search=st.text_input("🔍 Search ticker or company name across all markets",
                              placeholder="e.g. ENI, Volkswagen, ASML…")

    st.markdown('<div class="section-hdr">📈 Index Performance</div>',unsafe_allow_html=True)
    with st.spinner("Loading indices…"):
        idx_cols=st.columns(7)
        for i,(name,ticker) in enumerate(INDEX_TICKERS.items()):
            with idx_cols[i%7]:
                q=get_index_quote(ticker)
                if q and (q.get("close") or q.get("adjusted_close")):
                    chg=q.get("change_p",0)
                    try:    chg=float(chg) if chg is not None else 0.0
                    except: chg=0.0
                    px_val=q.get("close") or q.get("adjusted_close") or 0
                    try:    px_val=float(px_val)
                    except: px_val=0.0
                    color="#22d48a" if chg>=0 else "#e84560"
                    sign="+" if chg>=0 else ""
                    ts=q.get("timestamp","")
                    try:
                        from datetime import timezone
                        import zoneinfo
                        london_tz = zoneinfo.ZoneInfo("Europe/London")
                        ts_str = datetime.fromtimestamp(int(ts), tz=timezone.utc).astimezone(london_tz).strftime("%H:%M LON") if ts else "EOD"
                    except: ts_str="EOD"
                    st.markdown(f"""
                    <div style="background:#0d1017;border:1px solid #1e2840;padding:9px 11px;
                    border-radius:3px;margin-bottom:6px;">
                        <div style="font-size:7px;font-weight:700;letter-spacing:.08em;
                        text-transform:uppercase;color:#5a6880;margin-bottom:2px;">{name}</div>
                        <div style="font-family:'Fira Code',monospace;font-size:13px;
                        font-weight:600;color:{color};">{sign}{chg:.2f}%</div>
                        <div style="font-family:'Fira Code',monospace;font-size:8px;
                        color:#8a9ab8;">{px_val:,.1f} · {ts_str}</div>
                    </div>""",unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#0d1017;border:1px solid #1e2840;padding:9px 11px;
                    border-radius:3px;margin-bottom:6px;">
                        <div style="font-size:7px;color:#5a6880;">{name}</div>
                        <div style="font-size:10px;color:#5a6880;">N/A</div>
                    </div>""",unsafe_allow_html=True)

    st.markdown("---")

    with st.spinner("Loading all Eurozone prices…"):
        all_df = _load_all_prices()

    # Debug: mostra quanti titoli caricati per exchange
    if all_df.empty:
        st.error("No data loaded from EODHD. Check API key and connection.")
    else:
        # Diagnostica temporanea
        debug_info = []
        for code in EXCHANGES:
            n = len(all_df[all_df["Exchange"]==code])
            chg_ok = all_df[all_df["Exchange"]==code]["1D %"].notna().sum()
            debug_info.append(f"{EXCHANGES[code]['flag']} {code}: {n} stocks, {chg_ok} with 1D%")
        with st.expander("🔍 Debug data (remove before launch)", expanded=False):
            for d in debug_info:
                st.write(d)
            st.write(f"Total: {len(all_df)} stocks")
            st.write(f"1D % not null: {all_df['1D %'].notna().sum()}")
            st.write(f"Sample 1D % values: {all_df['1D %'].dropna().head(5).tolist()}")
            # Mostra i campi raw del bulk XETRA
            raw_xetra = get_bulk_eod("XETRA")
            if not raw_xetra.empty:
                st.write(f"Bulk XETRA columns: {list(raw_xetra.columns)}")
                st.write(f"Sample row: {raw_xetra.iloc[0].to_dict()}")

    u200 = all_df.copy() if not all_df.empty else pd.DataFrame()
    if not u200.empty:
        u200["_chg"] = pd.to_numeric(u200["1D %"],   errors="coerce")
        u200["_vol"] = pd.to_numeric(u200["Volume"], errors="coerce")
        u200["_px"]  = pd.to_numeric(u200["Price"],  errors="coerce")
        u200 = u200.nlargest(200, "_vol", keep="all")

    if not all_df.empty and not u200.empty:
        ew_chg = u200["_chg"].mean()  # equally weighted 1D return as live indicator

        kk=st.columns(4)
        kk[0].metric("Total Stocks — All Markets",    f"{len(all_df):,}")
        kk[1].metric("EW 1D Return (top 200 volume)", fp(ew_chg) if pd.notna(ew_chg) else "N/A")
        kk[2].metric("Gainers today (top 200)",       f"{int((u200['_chg']>0).sum())}")
        kk[3].metric("Losers today (top 200)",         f"{int((u200['_chg']<0).sum())}")
        st.markdown("---")

        if dash_search:
            q=dash_search.lower()
            matches=all_df[all_df["Ticker"].str.lower().str.contains(q,na=False)|
                           all_df["Company"].str.lower().str.contains(q,na=False)].head(30)
            if not matches.empty:
                st.markdown(f'<div class="section-hdr">🔍 "{dash_search}" — {len(matches)} results</div>',unsafe_allow_html=True)
                disp=matches[["Flag","Ticker","Company","Country","Price","1D %","Volume"]].copy()
                disp["Price"]=disp["Price"].apply(lambda x:fv(x,2))
                disp["1D %"]=disp["1D %"].apply(fp)
                disp["Volume"]=disp["Volume"].apply(lambda x:f"{int(x):,}" if pd.notna(x) else "—")
                st.dataframe(disp,use_container_width=True,hide_index=True)
                st.markdown("---")
            else:
                st.warning(f"No stocks found for '{dash_search}'")
                st.markdown("---")

        valid_u = u200[u200["_chg"].notna()]
        col1, col2 = st.columns(2)

        def show_mover(df_m, n, asc, color, label):
            m = df_m.nsmallest(n,"_chg") if asc else df_m.nlargest(n,"_chg")
            m = m[["Flag","Ticker","Company","Price","_chg","_vol"]].copy()
            m.columns = ["","Ticker","Company","Price €","1D %","Volume"]
            m["Price €"] = m["Price €"].apply(lambda x: fv(x,2))
            m["1D %"]    = m["1D %"].apply(fp)
            m["Volume"]  = m["Volume"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
            st.markdown(f'<div style="font-size:9px;font-weight:700;letter-spacing:.1em;color:{color};margin-bottom:6px;">{label}</div>', unsafe_allow_html=True)
            st.dataframe(m, use_container_width=True, hide_index=True)

        with col1: show_mover(valid_u, 10, False, "#22d48a", "🟢 TOP 10 GAINERS — ALL MARKETS")
        with col2: show_mover(valid_u, 10, True,  "#e84560", "🔴 TOP 10 LOSERS — ALL MARKETS")

        st.markdown("---")
        st.markdown('<div class="section-hdr">🚀 Top 10 — Best 1D Performance by Volume (top 200)</div>', unsafe_allow_html=True)
        st.caption("12-month momentum available in each national screen after clicking **Load & Apply**")
        top10m = valid_u.nlargest(10,"_chg")[["Flag","Ticker","Company","Price","_chg","_vol"]].copy()
        top10m.columns = ["","Ticker","Company","Price €","1D %","Volume"]
        top10m["Price €"] = top10m["Price €"].apply(lambda x: fv(x,2))
        top10m["1D %"]    = top10m["1D %"].apply(fp)
        top10m["Volume"]  = top10m["Volume"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
        st.dataframe(top10m, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown('<div class="section-hdr">Performance by Country Today</div>', unsafe_allow_html=True)
        country_rows = []
        for country, grp in u200.groupby("Country"):
            valid_grp = grp[grp["_chg"].notna()]
            if valid_grp.empty: continue
            ew_1d = valid_grp["_chg"].mean()
            meta  = next((v for v in EXCHANGES.values() if v["label"]==country), {})
            country_rows.append({
                "":        meta.get("flag",""),
                "Country": country,
                "Stocks":  len(valid_grp),
                "EW 1D %": ew_1d,
                "Best":    valid_grp.loc[valid_grp["_chg"].idxmax(), "Ticker"] if not valid_grp.empty else "-",
                "Worst":   valid_grp.loc[valid_grp["_chg"].idxmin(), "Ticker"] if not valid_grp.empty else "-",
            })
        if country_rows:
            ctbl = pd.DataFrame(country_rows).sort_values("EW 1D %", ascending=False)
            fig_c = px.bar(ctbl, x="Country", y="EW 1D %",
                color="EW 1D %",
                color_continuous_scale=["#e84560","#131720","#22d48a"],
                color_continuous_midpoint=0, template="plotly_dark",
                title="Today's Return by Country — Equally Weighted (top 200 by volume)")
            fig_c.update_layout(paper_bgcolor="#0d1017", plot_bgcolor="#07090d",
                font_color="#dde4f0", height=280, margin=dict(l=0,r=0,t=40,b=0),
                showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig_c, use_container_width=True)
            ctbl["EW 1D %"] = ctbl["EW 1D %"].apply(fp)
            st.dataframe(ctbl, use_container_width=True, hide_index=True)
            st.caption("💡 Sector breakdown with market cap weights available in each national screen after Load & Apply")
    else:
        st.warning("No market data. Press Refresh.")

# ── EUROZONE ─────────────────────────────────────────────────────
elif page=="🌍 Eurozone Screen":
    st.markdown("""<div style="background:linear-gradient(135deg,#0d1017,#131720);border-bottom:1px solid #1e2840;
    padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">
        <span style="font-size:28px;">🌍</span>
        <div><div style="font-size:16px;font-weight:700;color:#dde4f0;">Eurozone — All Markets Screen</div>
        <div style="font-size:10px;color:#5a6880;">Set filters → Load & Apply → Full fundamentals for filtered stocks</div></div>
    </div>""",unsafe_allow_html=True)
    with st.spinner("Loading all Eurozone prices…"):
        frames_ez=[]
        for code in EXCHANGES:
            df_ex=build_exchange_df(code)
            if not df_ex.empty: frames_ez.append(df_ex)
        ez_df=pd.concat(frames_ez,ignore_index=True) if frames_ez else pd.DataFrame()
    show_screener(ez_df,title=f"🌍 Eurozone — {len(ez_df)} stocks",exchange_code="EZ")

# ── SINGLE EXCHANGE ───────────────────────────────────────────────
elif page in PAGE_TO_EXCHANGE:
    exch_code=PAGE_TO_EXCHANGE[page]
    exch_meta=EXCHANGES.get(exch_code,{})
    flag=exch_meta.get("flag",""); market=exch_meta.get("market","")
    st.markdown(f"""<div style="background:linear-gradient(135deg,#0d1017,#131720);border-bottom:1px solid #1e2840;
    padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">
        <span style="font-size:28px;">{flag}</span>
        <div><div style="font-size:16px;font-weight:700;color:#dde4f0;">{market}</div>
        <div style="font-size:10px;color:#5a6880;">Set filters → Load & Apply → Full fundamentals</div></div>
    </div>""",unsafe_allow_html=True)
    with st.spinner(f"Loading {market} prices…"):
        df_exch=build_exchange_df(exch_code)
    show_screener(df_exch,title=f"{flag} {market} — {len(df_exch)} stocks",exchange_code=exch_code)

# ── PORTFOLIOS ────────────────────────────────────────────────────
elif page=="💼 Portfolios":
    st.markdown('<div class="section-hdr">💼 Portfolio Management</div>',unsafe_allow_html=True)
    st.info("⚠️ **Beta note:** Portfolios are stored in your browser session only. They will be lost when you close the browser. Persistent storage will be available in the full version.")

    if "portfolios" not in st.session_state:
        st.session_state.portfolios={"Portfolio 1":{},"Portfolio 2":{},"Portfolio 3":{}}

    pf_names=list(st.session_state.portfolios.keys())
    c_sel,c_new=st.columns([3,2])
    with c_sel: active_pf=st.selectbox("Active portfolio",pf_names)
    with c_new:
        new_pf_name=st.text_input("New portfolio name",placeholder="e.g. Growth EU")
        if st.button("+ Create") and new_pf_name and len(st.session_state.portfolios)<10:
            st.session_state.portfolios[new_pf_name]={}
            st.rerun()

    st.markdown("---")
    st.caption("Italian stocks: **ENI.XETRA**, **ENEL.XETRA**, **ISP.XETRA**, **STM.XETRA**")
    a1,a2,a3,a4=st.columns([3,1,1,1])
    with a1: ticker_input=st.text_input("EODHD Ticker",placeholder="ENI.XETRA, SAP.XETRA, ASML.AS")
    with a2: qty_input=st.number_input("Qty",min_value=0.0,step=1.0)
    with a3: cost_input=st.number_input("Buy price €",min_value=0.0,step=0.01)
    with a4:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("+ Add"):
            if qty_input>0 and cost_input>0 and ticker_input:
                pf=st.session_state.portfolios[active_pf]
                if len(pf)>=50: st.error("Max 50 stocks")
                else:
                    pf[ticker_input]={"qty":qty_input,"cost":cost_input}
                    st.success(f"Added {ticker_input}")
                    st.rerun()

    pf_data=st.session_state.portfolios.get(active_pf,{})
    if not pf_data:
        st.info("No stocks yet. Add above or from any screen.")
    else:
        with st.spinner("Loading prices…"):
            rows=[]; total_cost=total_curr=total_1d=0
            for full_ticker,h in pf_data.items():
                q=eodhd_get(f"real-time/{full_ticker}")
                if isinstance(q,list): q=q[0] if q else {}
                if not q: q={}
                px=q.get("close") or q.get("adjusted_close") or h["cost"]
                chg_p=q.get("change_p",0)
                try:    chg_p=float(chg_p) if chg_p is not None else 0.0
                except: chg_p=0.0
                try:    px=float(px)
                except: px=float(h["cost"])
                qty=h["qty"]; cost_px=h["cost"]
                cost_val=qty*cost_px; curr_val=qty*px
                pnl=curr_val-cost_val; pnl_pct=pnl/cost_val*100 if cost_val else 0
                pnl_1d=curr_val*chg_p/100
                total_cost+=cost_val; total_curr+=curr_val; total_1d+=pnl_1d
                rows.append({"Ticker":full_ticker,"Qty":qty,"Buy Price €":cost_px,
                    "Cost Value €":cost_val,"Current Price €":px,"Market Value €":curr_val,
                    "Weight %":None,"P&L €":pnl,"P&L %":pnl_pct,"P&L Today €":pnl_1d})
            for r in rows:
                r["Weight %"]=r["Market Value €"]/total_curr*100 if total_curr else 0

        k1,k2,k3,k4=st.columns(4)
        k1.metric("Invested",    f"€ {total_cost:,.0f}")
        k2.metric("Market Value",f"€ {total_curr:,.0f}",fp((total_curr-total_cost)/total_cost*100) if total_cost else "—")
        k3.metric("Total P&L",  f"€ {total_curr-total_cost:+,.0f}",fp((total_curr-total_cost)/total_cost*100) if total_cost else "—")
        k4.metric("P&L Today",  f"€ {total_1d:+,.0f}")
        st.markdown("---")
        pf_df=pd.DataFrame(rows)
        ch1,ch2=st.columns(2)
        with ch1:
            exch_d=pf_df.groupby(pf_df["Ticker"].str.split(".").str[-1])["Market Value €"].sum().reset_index()
            exch_d.columns=["Exchange","Value €"]
            fig=px.pie(exch_d,values="Value €",names="Exchange",title="By Exchange",template="plotly_dark",color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(paper_bgcolor="#0d1017",plot_bgcolor="#0d1017",font_color="#dde4f0",height=260,margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig,use_container_width=True)
        with ch2:
            fig2=px.bar(pf_df.sort_values("P&L %",ascending=False),x="Ticker",y="P&L %",
                color="P&L %",color_continuous_scale=["#e84560","#131720","#22d48a"],
                color_continuous_midpoint=0,title="P&L % per stock",template="plotly_dark")
            fig2.update_layout(paper_bgcolor="#0d1017",plot_bgcolor="#0d1017",font_color="#dde4f0",height=260,margin=dict(l=0,r=0,t=30,b=40),showlegend=False,coloraxis_showscale=False)
            st.plotly_chart(fig2,use_container_width=True)
        disp=pf_df.copy()
        for c in ["Buy Price €","Current Price €"]: disp[c]=disp[c].apply(lambda x:fv(x,2))
        for c in ["Cost Value €","Market Value €","P&L €","P&L Today €"]:
            disp[c]=disp[c].apply(lambda x:f"€ {x:+,.0f}" if pd.notna(x) else "—")
        for c in ["Weight %","P&L %"]: disp[c]=disp[c].apply(lambda x:fp(x,1))
        disp["Qty"]=disp["Qty"].apply(lambda x:f"{x:,.0f}")
        st.dataframe(disp,use_container_width=True,hide_index=True)
        rm_sel=st.selectbox("Remove stock",list(pf_data.keys()))
        if st.button("🗑️ Remove"):
            del st.session_state.portfolios[active_pf][rm_sel]
            st.rerun()

# ── LEGAL ────────────────────────────────────────────────────────
elif page=="📋 Legal":
    tab1,tab2,tab3,tab4=st.tabs(["Terms of Use","Privacy Policy","Cookie Policy","Disclaimer"])
    with tab1: st.markdown(TERMS_OF_USE)
    with tab2: st.markdown(PRIVACY_POLICY)
    with tab3: st.markdown(COOKIE_POLICY)
    with tab4: st.markdown(DISCLAIMER)

# ── FOOTER ───────────────────────────────────────────────────────
st.markdown(FOOTER_HTML, unsafe_allow_html=True)
st.markdown(COOKIE_BANNER_HTML, unsafe_allow_html=True)
