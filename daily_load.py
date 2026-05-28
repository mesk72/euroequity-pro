# ============================================================
# FORWARDALPHA — DAILY LOAD
# Da eseguire ogni sera dopo la chiusura dei mercati europei
# Tempo stimato: 35-40 minuti
# ============================================================

import yfinance as yf
import requests
import pandas as pd
import numpy as np
import json
import time
import math
from datetime import datetime, timedelta

# ── CONFIGURAZIONE ──────────────────────────────────────────
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = input("Inserisci Supabase Service Key: ")
TODAY = datetime.now().strftime("%Y-%m-%d")

headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

SUFFIX_MAP = {
    "MIL":".MI","XETRA":".DE","PA":".PA","AS":".AS","MC":".MC",
    "BR":".BR","LS":".LS","VI":".VI","HE":".HE","IR":".IR","AT":".AT",
    "LSE":".L","AIM":".L","SWX":".SW","OM":".ST","NGM":".ST",
    "OB":".OL","CPSE":".CO"
}
SPECIAL_TICKERS = {
    "BP.":"BP.L","RR.":"RR.L","BT.A":"BT-A.L","BA.":"BA.L",
    "NG.":"NG.L","AO.":"AO.L","VP.":"VP.L","QQ.":"QQ.L","SN.":"SN.L",
}

def sym(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    return ticker.replace(" ","-") + SUFFIX_MAP.get(exchange,"")

def safe_float(v):
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except: return None

def safe_int(v):
    try:
        f = float(v)
        return 0 if math.isnan(f) or math.isinf(f) else int(f)
    except: return 0

def ts(t):
    try: return datetime.fromtimestamp(t).strftime("%Y-%m-%d")
    except: return None

# ── LEGGE UNIVERSO ──────────────────────────────────────────
print("=" * 60)
print(f"FORWARDALPHA DAILY LOAD — {TODAY}")
print("=" * 60)

all_stocks = []
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange","offset":offset,"limit":1000})
    data = r.json()
    if not data: break
    all_stocks.extend(data)
    offset += 1000
    if len(data) < 1000: break
print(f"\nUniverso: {len(all_stocks)} titoli")

# ============================================================
# STEP 1 — PREZZI EOD + MOMENTUM
# ============================================================
print("\n[1/5] Download prezzi EOD...")

ok=fail=0
price_buf=[]

for stock in all_stocks:
    ticker = stock["ticker"]
    exchange = stock["exchange"]
    s = sym(ticker, exchange)

    r = requests.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":"eq."+ticker,"exchange":"eq."+exchange,
                "order":"date.desc","limit":1})
    data = r.json()
    last = data[0]["date"] if data else "2021-05-25"

    if last >= TODAY:
        ok += 1
        continue

    start = (datetime.strptime(last,"%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        df = yf.download(s, start=start, end=TODAY, progress=False, auto_adjust=True)
        if df.empty: raise Exception("empty")
        if hasattr(df.columns,"get_level_values"): df.columns=df.columns.get_level_values(0)
        df = df.reset_index()
        for _,row in df.iterrows():
            cv = safe_float(row["Close"])
            if cv is None: continue
            price_buf.append({
                "ticker":ticker,"exchange":exchange,
                "date":row["Date"].strftime("%Y-%m-%d"),
                "open":safe_float(row.get("Open",cv)) or cv,
                "high":safe_float(row.get("High",cv)) or cv,
                "low":safe_float(row.get("Low",cv)) or cv,
                "close":cv,"adj_close":cv,
                "volume":safe_int(row.get("Volume",0))
            })
        ok += 1
    except: fail += 1

    if len(price_buf) >= 500:
        requests.post(SUPABASE_URL+"/rest/v1/prices_eod",
            headers=headers_up, json=price_buf)
        price_buf = []
    if (ok+fail) % 200 == 0:
        print(f" prezzi ok={ok} fail={fail}")
    time.sleep(0.05)

if price_buf:
    requests.post(SUPABASE_URL+"/rest/v1/prices_eod",
        headers=headers_up, json=price_buf)
print(f" Prezzi completati: ok={ok} fail={fail}")

# ── CALCOLA MOMENTUM ────────────────────────────────────────
print("\n Calcolo momentum...")
ok=fail=0
mom_updates=[]

for stock in all_stocks:
    ticker = stock["ticker"]
    exchange = stock["exchange"]

    r = requests.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":"eq."+ticker,
                "exchange":"eq."+exchange,"date":"lte."+TODAY,
                "order":"date.desc","limit":260})
    data = r.json()
    if not data: fail+=1; continue

    closes = [d["adj_close"] for d in data if d["adj_close"]]
    if not closes: fail+=1; continue

    last_px = closes[0]

    def mom(n):
        if len(closes) >= n and closes[n-1]:
            return round(last_px/closes[n-1]-1, 6)
        return None

    chg1d = round((closes[0]/closes[1]-1)*100, 4) if len(closes)>=2 else None

    mom_updates.append({
        "ticker":ticker,"exchange":exchange,
        "mom1w":mom(5),"mom1m":mom(21),
        "mom6m":mom(126),"mom12m":mom(252),
        "change1d":chg1d
    })
    ok+=1

for i in range(0,len(mom_updates),100):
    requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up, json=mom_updates[i:i+100])
print(f" Momentum ok={ok} fail={fail}")

# ============================================================
# STEP 2 — NEXT EARNINGS DATE
# ============================================================
print("\n[2/5] Download next earnings date...")

ok=fail=no_date=0
earn_updates=[]

for stock in all_stocks:
    ticker = stock["ticker"]
    exchange = stock["exchange"]
    s = sym(ticker, exchange)

    info = None
    for attempt in range(3):
        try:
            info = yf.Ticker(s).info
            break
        except Exception as e:
            if '500' in str(e) or '429' in str(e):
                time.sleep(3)
                continue
            break

    if info:
        next_earn = ts(info.get("earningsTimestampStart"))
        if next_earn and next_earn >= "2026-01-01":
            earn_updates.append({
                "ticker":ticker,"exchange":exchange,
                "next_report":next_earn
            })
            ok+=1
        else:
            no_date+=1
    else:
        fail+=1

    if (ok+no_date+fail) % 200 == 0:
        print(f" earnings ok={ok} no_date={no_date} fail={fail}")
    time.sleep(0.3)

for i in range(0,len(earn_updates),100):
    requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up, json=earn_updates[i:i+100])
print(f" Earnings ok={ok} no_date={no_date} fail={fail}")

# ============================================================
# STEP 3 — CAMBI FX
# ============================================================
print("\n[3/5] Download cambi FX...")

FX_PAIRS = {
    "EURGBP=X":"EURGBP","EURCHF=X":"EURCHF","EURSEK=X":"EURSEK",
    "EURNOK=X":"EURNOK","EURDKK=X":"EURDKK","EURUSD=X":"EURUSD",
    "GBPUSD=X":"GBPUSD"
}
fx_rates = {"date": TODAY}
for pair_sym, pair_name in FX_PAIRS.items():
    try:
        info = yf.Ticker(pair_sym).info
        rate = info.get("regularMarketPrice") or info.get("previousClose")
        fx_rates[pair_name] = rate
        print(f" {pair_name}: {rate}")
    except: pass
    time.sleep(0.2)

requests.post(SUPABASE_URL+"/rest/v1/fx_rates",
    headers=headers_up, json=[fx_rates])
print(" Cambi FX salvati")

# ============================================================
# STEP 4 — CARICA CSV TIKR E CALCOLA FONDAMENTALI
# ============================================================
print("\n[4/5] Carica CSV TIKR e calcola fondamentali...")

from google.colab import files
uploaded = files.upload()
csv_name = list(uploaded.keys())[0]
df = pd.read_csv(csv_name)
print(f" CSV caricato: {len(df)} righe")

def parse_num(v):
    if pd.isna(v): return None
    s = str(v).strip().replace(',','').replace('$','').replace('%','').replace('x','')
    if s in ('','-','N/A','nan','—'): return None
    if s.startswith('(') and s.endswith(')'): s = '-' + s[1:-1]
    try: return float(s)
    except: return None

COL_MAP = {
    'ticker': 'Ticker',
    'exchange': 'Primary Exchange',
    'mkt_cap': 'Last Market Capitalization',
    'price_usd': 'Last Close Price',
    'pb': 'Trailing P/BVPS LTM',
    'pe_trail_tikr':'Trailing P/Diluted EPS before Extra LTM',
    'eps_fy24': 'EPS Normalized (FY 2024)',
    'eps_fy25': 'EPS Normalized (FY 2025)',
    'eps_fy26': 'Mean EPS Normalized (FY 2026)',
    'eps_fy27': 'Mean EPS Normalized (FY 2027)',
    'eps_fy28': 'Mean EPS Normalized (FY 2028)',
    'eps_cy25': 'EPS Normalized (CY 2025)',
    'eps_cy26': 'Mean EPS Normalized (CY 2026)',
    'eps_cy27': 'Mean EPS Normalized (CY 2027)',
    'rev_fy24': 'Revenue (FY 2024)',
    'rev_fy25': 'Revenue (FY 2025)',
    'rev_fy26': 'Mean Revenue (FY 2026)',
    'rev_fy27': 'Mean Revenue (FY 2027)',
    'rev_fy28': 'Mean Revenue (FY 2028)',
    'rev_cy25': 'Revenue (CY 2025)',
    'rev_cy26': 'Mean Revenue (CY 2026)',
    'rev_cy27': 'Mean Revenue (CY 2027)',
}

# Mappa exchange TIKR -> nostro DB
EXCHANGE_MAP = {
    'ENXTAM':'AS', 'ENXTPA':'PA', 'ENXTBR':'BR', 'ENXTLS':'LS',
    'XTRA':'XETRA', 'BIT':'MIL', 'HLSE':'HE', 'WBAG':'VI',
    'ISE':'IR', 'ATSE':'AT', 'BME':'MC', 'DB':'XETRA',
    'DUSE':'XETRA', 'MUN':'XETRA', 'BST':'XETRA',
    'SWX':'SWX', 'LSE':'LSE', 'AIM':'AIM', 'OM':'OM',
    'NGM':'NGM', 'OB':'OB', 'CPSE':'CPSE',
    'HMSE':'OM', 'HNSE':'OB',
}

# Legge next earnings da Supabase
next_earn_map = {}
offset = 0
while True:
    r = requests.get(SUPABASE_URL+"/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,next_report","offset":offset,"limit":1000})
    data = r.json()
    if not data: break
    for d in data:
        if d.get("next_report"):
            next_earn_map[(d["ticker"],d["exchange"])] = d["next_report"]
    offset+=1000
    if len(data)<1000: break
print(f" Next earnings: {len(next_earn_map)}")

today_dt = datetime.strptime(TODAY, "%Y-%m-%d")
MONTH = today_dt.month
fund_updates = []

for _, row in df.iterrows():
    ticker = str(row.get(COL_MAP['ticker'],'') or '').strip()
    exchange_tikr = str(row.get(COL_MAP['exchange'],'') or '').strip()
    exchange = EXCHANGE_MAP.get(exchange_tikr, exchange_tikr)
    if not ticker or not exchange: continue

    price_usd = parse_num(row.get(COL_MAP['price_usd']))
    mkt_cap = parse_num(row.get(COL_MAP['mkt_cap']))
    pb = parse_num(row.get(COL_MAP['pb']))
    pe_trail_tikr = parse_num(row.get(COL_MAP['pe_trail_tikr']))

    eps_fy = {24:parse_num(row.get(COL_MAP['eps_fy24'])),
              25:parse_num(row.get(COL_MAP['eps_fy25'])),
              26:parse_num(row.get(COL_MAP['eps_fy26'])),
              27:parse_num(row.get(COL_MAP['eps_fy27'])),
              28:parse_num(row.get(COL_MAP['eps_fy28']))}

    eps_cy = {25:parse_num(row.get(COL_MAP['eps_cy25'])),
              26:parse_num(row.get(COL_MAP['eps_cy26'])),
              27:parse_num(row.get(COL_MAP['eps_cy27']))}

    rev_fy = {24:parse_num(row.get(COL_MAP['rev_fy24'])),
              25:parse_num(row.get(COL_MAP['rev_fy25'])),
              26:parse_num(row.get(COL_MAP['rev_fy26'])),
              27:parse_num(row.get(COL_MAP['rev_fy27'])),
              28:parse_num(row.get(COL_MAP['rev_fy28']))}

    rev_cy = {25:parse_num(row.get(COL_MAP['rev_cy25'])),
              26:parse_num(row.get(COL_MAP['rev_cy26'])),
              27:parse_num(row.get(COL_MAP['rev_cy27']))}

    next_report = next_earn_map.get((ticker, exchange))
    eps_ltm = eps_ntm = rev_ltm = rev_ntm = None
    W_CURR = (12-MONTH+1)/12
    W_NEXT = 1-W_CURR

    if next_report and next_report >= "2026-01-01":
        next_dt = datetime.strptime(next_report, "%Y-%m-%d")
        last_report = next_dt - timedelta(days=365) if next_dt > today_dt else next_dt
        diff_days = (today_dt - last_report).days
        N = diff_days // 365
        W1 = (diff_days % 365) / 365
        W2 = 1 - W1

        fy0,fy1,fy2 = 25+N, 26+N, 27+N

        # EPS LTM — formula FY
        if eps_fy.get(fy0) is not None and eps_fy.get(fy1) is not None:
            eps_ltm = W2*eps_fy[fy0] + W1*eps_fy[fy1]
        elif eps_fy.get(fy0) is not None:
            eps_ltm = eps_fy[fy0]
        # fallback CY
        if eps_ltm is None and eps_cy.get(25) is not None and eps_cy.get(26) is not None:
            eps_ltm = W_CURR*eps_cy[25] + W_NEXT*eps_cy[26]

        # EPS NTM — formula FY
        if eps_fy.get(fy1) is not None and eps_fy.get(fy2) is not None:
            eps_ntm = W2*eps_fy[fy1] + W1*eps_fy[fy2]
        elif eps_fy.get(fy1) is not None:
            eps_ntm = eps_fy[fy1]
        # fallback CY
        if eps_ntm is None and eps_cy.get(26) is not None and eps_cy.get(27) is not None:
            eps_ntm = W_CURR*eps_cy[26] + W_NEXT*eps_cy[27]

        # REV LTM — formula FY
        if rev_fy.get(fy0) is not None and rev_fy.get(fy1) is not None:
            rev_ltm = W2*rev_fy[fy0] + W1*rev_fy[fy1]
        if rev_ltm is None and rev_cy.get(25) is not None and rev_cy.get(26) is not None:
            rev_ltm = W_CURR*rev_cy[25] + W_NEXT*rev_cy[26]

        # REV NTM — formula FY
        if rev_fy.get(fy1) is not None and rev_fy.get(fy2) is not None:
            rev_ntm = W2*rev_fy[fy1] + W1*rev_fy[fy2]
        if rev_ntm is None and rev_cy.get(26) is not None and rev_cy.get(27) is not None:
            rev_ntm = W_CURR*rev_cy[26] + W_NEXT*rev_cy[27]

    else:
        # Fallback CY completo
        if eps_cy.get(25) is not None and eps_cy.get(26) is not None:
            eps_ltm = W_CURR*eps_cy[25] + W_NEXT*eps_cy[26]
        if eps_cy.get(26) is not None and eps_cy.get(27) is not None:
            eps_ntm = W_CURR*eps_cy[26] + W_NEXT*eps_cy[27]
        if rev_cy.get(25) is not None and rev_cy.get(26) is not None:
            rev_ltm = W_CURR*rev_cy[25] + W_NEXT*rev_cy[26]
        if rev_cy.get(26) is not None and rev_cy.get(27) is not None:
            rev_ntm = W_CURR*rev_cy[26] + W_NEXT*rev_cy[27]

    if price_usd and eps_ltm and eps_ltm != 0:
        pe_our = price_usd/eps_ltm
        if abs(pe_our) > 500:
            pe_trailing = pe_trail_tikr
        elif pe_trail_tikr and pe_trail_tikr != 0:
            # Se TIKR negativo e nostro positivo → nostro (GAAP vs Normalized)
            if pe_trail_tikr < 0 and pe_our > 0:
                pe_trailing = pe_our
            # Se differenza > 3% usiamo TIKR
            else:
                diff_pct = abs(pe_our - pe_trail_tikr) / abs(pe_trail_tikr)
                pe_trailing = pe_trail_tikr if diff_pct > 0.03 else pe_our
        else:
            pe_trailing = pe_our
    else:
        pe_trailing = pe_trail_tikr

    if price_usd and eps_ntm and eps_ntm != 0:
        pe_forward = price_usd/eps_ntm
        if abs(pe_forward)>500: pe_forward=None
    else:
        pe_forward = None

    eps_growth = None
    if eps_ltm and eps_ntm and eps_ltm != 0:
        if eps_ltm > 0 and eps_ntm < 0:
            eps_growth = None # da positivo a negativo — non interpretabile
        else:
            eps_growth = round(eps_ntm / abs(eps_ltm) - 1, 6)

    rev_growth = None
    if rev_ltm and rev_ntm and rev_ltm>0:
        rev_growth = round(rev_ntm/rev_ltm-1, 6)

    fund_updates.append({
        "ticker":ticker,"exchange":exchange,"mkt_cap":mkt_cap,"pb":pb,
        "pe_trailing":round(pe_trailing,2) if pe_trailing else None,
        "pe_forward": round(pe_forward,2) if pe_forward else None,
        "eps_growth": eps_growth,"rev_growth":rev_growth,
    })

ok=0
for i in range(0,len(fund_updates),100):
    r=requests.post(SUPABASE_URL+"/rest/v1/fundamentals",headers=headers_up,json=fund_updates[i:i+100])
    if r.status_code in (200,201,204): ok+=len(fund_updates[i:i+100])
print(f" Fondamentali aggiornati: {ok}/{len(fund_updates)}")

# ============================================================
# STEP 5 — RICALCOLA RANK
# ============================================================
print("\n[5/5] Ricalcolo rank Value/Growth Score...")

# Salva rank correnti in _prev prima di sovrascrivere
print(" Salvataggio rank precedenti...")
prev_data=[]
offset=0
while True:
    r=requests.get(SUPABASE_URL+"/rest/v1/fundamentals",headers=headers_r,
        params={"select":"ticker,exchange,value_score,growth_score",
                "offset":offset,"limit":1000})
    data=r.json()
    if not data: break
    for d in data:
        if d.get("value_score") is not None or d.get("growth_score") is not None:
            prev_data.append({
                "ticker":d["ticker"],"exchange":d["exchange"],
                "value_score_prev":d.get("value_score"),
                "growth_score_prev":d.get("growth_score")
            })
    offset+=1000
    if len(data)<1000: break
ok=0
for i in range(0,len(prev_data),100):
    r=requests.post(SUPABASE_URL+"/rest/v1/fundamentals",
        headers=headers_up,json=prev_data[i:i+100])
    if r.status_code in (200,201,204): ok+=len(prev_data[i:i+100])
print(f" Rank precedenti salvati: {ok}/{len(prev_data)}")

# Legge tutti i fondamentali + momentum
all_data=[]
offset=0
while True:
    r=requests.get(SUPABASE_URL+"/rest/v1/fundamentals",headers=headers_r,
        params={"select":"ticker,exchange,pe_trailing,pe_forward,pb,eps_growth,rev_growth,mom6m,mom12m",
                "offset":offset,"limit":1000})
    data=r.json()
    if not data: break
    all_data.extend(data)
    offset+=1000
    if len(data)<1000: break

# Legge mom1w e mom1m
mom_data=[]
offset=0
while True:
    r=requests.get(SUPABASE_URL+"/rest/v1/fundamentals",headers=headers_r,
        params={"select":"ticker,exchange,mom1w,mom1m","offset":offset,"limit":1000})
    data=r.json()
    if not data: break
    mom_data.extend(data)
    offset+=1000
    if len(data)<1000: break

mom1w_map={(d["ticker"],d["exchange"]):d.get("mom1w") for d in mom_data}
mom1m_map={(d["ticker"],d["exchange"]):d.get("mom1m") for d in mom_data}

# Gruppi rank per country
RANK_GROUPS = {
    'ITA':['MIL'],
    'DEU':['XETRA'],
    'FRA':['PA'],
    'GBR':['LSE','AIM'],
    'SWE':['OM'],
    'NOR':['OB'],
    'CHE':['SWX'],
    'NLD':['AS'],
    'BEL':['BR'],
    'FIN':['HE'],
    'ESP':['MC'],
    'DNK':['CPSE'],
}
NO_RANK = {'AT','VI','LS','IR','NGM'}

def pct_rank(values,v,invert=False):
    if v is None: return None
    try:
        if math.isnan(float(v)): return None
    except: return None
    valid=[x for x in values if x is not None]
    if not valid: return None
    below=sum(1 for x in valid if x<v)
    rank=below/len(valid)*100
    return int(round(100-rank if invert else rank))

def ey(pe):
    if pe is None or pe==0: return None
    try:
        if math.isnan(float(pe)): return None
    except: return None
    if abs(pe)>200: return None
    return 1.0/pe

def calc_ranks_for_group(group):
    ey_trail_g =[ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
    ey_fwd_g =[ey(d["pe_forward"]) for d in group if ey(d["pe_forward"]) is not None]
    pb_g =[d["pb"] for d in group if d["pb"] is not None and not math.isnan(float(d["pb"])) and d["pb"]<50]
    eps_g_vals =[d["eps_growth"] for d in group if d["eps_growth"] is not None and not math.isnan(float(d["eps_growth"]))]
    rev_g_vals =[d["rev_growth"] for d in group if d["rev_growth"] is not None and not math.isnan(float(d["rev_growth"]))]
    mom6_adj_g =[]
    mom12_adj_g=[]
    for d in group:
        key=(d["ticker"],d["exchange"])
        m6=d.get("mom6m"); m12=d.get("mom12m")
        m1w=mom1w_map.get(key); m1m=mom1m_map.get(key)
        if m6 is not None and m1w is not None: mom6_adj
