
# FORWARDALPHA_CONTEXT.md
# Leggere TUTTO prima di toccare qualsiasi codice in questa sessione

---

## REGOLE ASSOLUTE — MAI VIOLARE

1. PREZZI: tutti i prezzi EU/US/APAC → SOLO tabella `prices_eod` (ticker, exchange, date, adj_close). MAI price_history come destinazione.
2. PAGINAZIONE prices_eod: NON paginare tutta la tabella senza filtro ticker — va in timeout. Leggere sempre i ticker da `stocks` poi caricare prezzi in chunk da 20 con ticker=in.(t1,t2,...).
3. TICKER SEHK: nel DB sono SENZA leading zeros (700 non 0700). Sempre lstrip('0') ai ticker TIKR prima del match.
4. book_yield = 1/pb: NESSUN limite, NESSUNA eccezione. PB negativo → book_yield negativo → rank bassissimo automaticamente. PB positivo basso → rank altissimo. Formula: pct_rank(by_g, book_yield(pb)).
5. fiscal_month DINAMICO: se pub_date<=oggi e fy_end.year>=2026 → fy0=FY2026, fy1=FY2027, fy2=FY2028. Altrimenti fy0=FY2025, fy1=FY2026, fy2=FY2027.
6. pb<50 VIETATO: nessun filtro su PB.
7. PATCH non POST: per aggiornare dati esistenti usare sempre PATCH.
8. in_universe APAC: settato via SQL INSERT, non via script Python che pagina prices_eod.
9. APAC price su stock page: viene da fundamentals.price non da stocks.price.
10. EY negativi: inclusi sempre, nessun caso speciale.

---

## STACK TECNICO

- Frontend: Next.js 14, Vercel Pro
- Database: Supabase (mlqkisnizgyvvqajdvbh.supabase.co)
- Repo: github.com/mesk72/euroequity-pro
- Font: IBM Plex Sans, IBM Plex Mono, IBM Plex Sans Condensed
- Colori: bg #0d1017, surface #111827, orange #f59e0b, green #22d48a, red #e84560

---

## TABELLE SUPABASE

- stocks: ticker, exchange, company, sector, country, flag, website, description, in_universe, price, last_price_date, primary_exchange, yahoo_ticker
- fundamentals: ticker, exchange, price, change1d, mkt_cap, pe_trailing, pe_forward, pb, eps_growth, rev_growth, value_score, growth_score, combined_rank, rank_pe_ltm, rank_pe_ntm, rank_pb, rank_eps_gr, rank_rev_gr, mom1w, mom1m, mom6m, mom12m, rank_mom6_adj, rank_mom12_adj, fiscal_month
- prices_eod: ticker, exchange, date, adj_close — UNICA fonte prezzi
- fx_rates, daily_log

---

## ALLINEAMENTO stocks/prices_eod APAC (eseguito 21/06/2026)

Eseguire in Supabase SQL Editor se stocks e prices_eod si disallineano:

```sql
INSERT INTO stocks (ticker, exchange, flag, country, in_universe)
SELECT DISTINCT p.ticker, p.exchange,
  CASE p.exchange
    WHEN 'TSE' THEN '🇯🇵'
    WHEN 'SEHK' THEN '🇭🇰'
    WHEN 'TSX' THEN '🇨🇦'
    WHEN 'ASX' THEN '🇦🇺'
  END,
  CASE p.exchange
    WHEN 'TSE' THEN 'JPN'
    WHEN 'SEHK' THEN 'HKG'
    WHEN 'TSX' THEN 'CAN'
    WHEN 'ASX' THEN 'AUS'
  END,
  false
FROM prices_eod p
LEFT JOIN stocks s ON s.ticker = p.ticker AND s.exchange = p.exchange
WHERE p.exchange IN ('TSE','SEHK','TSX','ASX')
AND s.ticker IS NULL;

Parse_num

def parse_num(v):
    if v is None: return None
    try:
        if pd.isna(v): return None
    except: pass
    s = str(v).strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1]
    s = s.replace('$','').replace(',','').replace('x','').replace('%','').strip()
    if s in ['-','','N/A','nm',chr(8212)]: return None
    try:
        f = float(s)
        if math.isnan(f) or math.isinf(f): return None
        return -f if negative else f
    except: return None

Pct_rank

def pct_rank(vals, v):
    if v is None or not vals: return None
    below = sum(1 for x in vals if x < v)

Earning_yield

def ey(pe):
    if pe is None or pe == 0: return None
    return 1.0 / pe # PE negativi inclusi sempre
    return round(below / len(vals) * 100)

Book_yield formula corretta 

def book_yield(pb):
    if pb is None or pb == 0: return None
    return 1.0 / pb
# PB negativo → book_yield negativo → rank bassissimo ✓
# PB = 0.5 → book_yield = 2.0 → rank altissimo ✓
# PB = 50 → book_yield = 0.02 → rank basso ✓


FORMULA VALUE SCORE
r_eyt = pct_rank(ey_trail_g, ey(pe_trailing))
r_eyf = pct_rank(ey_fwd_g, ey(pe_forward))
r_pb = pct_rank(by_g, book_yield(pb))
Minimo 2 su 3
value_score = pct_rank(val_sums, sum(val_inputs))

FORMULA GROWTH SCORE
r_epsg = pct_rank(eps_g, eps_growth)
r_revg = pct_rank(rev_g, rev_growth)
r_m6 = pct_rank(m6_g, mom6m - mom1w)
r_m12 = pct_rank(m12_g, mom12m - mom1m)
Minimo 3 su 4
growth_score = pct_rank(gr_sums, sum(gr_inputs))

FORMULA COMBINED/BEST
Solo se ha ENTRAMBI value_score AND growth_score
combined_rank = pct_rank(comb_arr, value_score + growth_score)
Combined AP = TSE+SEHK+ASX insieme
Canada (TSX) = None (calcolato con US nel weekly_us)

CALENDARIZZAZIONE EPS/REVENUE

def calendarize(fy_month, fy2025, fy2026, fy2027, fy2028, today_dt):
    fm = int(fy_month) if fy_month else 12
    last_day = 28 if fm==2 else 30 if fm in [4,6,9,11] else 31
    fy_end = datetime(today_dt.year, fm, last_day)
    if fy_end > today_dt:
        fy_end = datetime(today_dt.year - 1, fm, last_day)
    pub_date = fy_end + timedelta(days=60)
    if pub_date > today_dt:
        return None, None, True # not_yet → eps_growth = fy3/|fy2| - 1
    if fy_end.year >= 2026:
        v0, v1, v2 = fy2026, fy2027, fy2028
    else:
        v0, v1, v2 = fy2025, fy2026, fy2027
    next_pub = datetime(pub_date.year+1, pub_date.month, pub_date.day)
    days_since = (today_dt - pub_date).days
    days_total = (next_pub - pub_date).days
    w_next = days_since / days_total
    w_curr = 1 - w_next
    ltm = w_curr*v0 + w_next*v1 if v0 is not None and v1 is not None else None
    ntm = w_curr*v1 + w_next*v2 if v1 is not None and v2 is not None else None
    return ltm, ntm, False

Esempi (oggi 21/06/2026)
FY dic 2025: pub=28/02/2026 → fy0=FY2025, ntm=0.691×FY2026+0.309×FY2027
FY mar 2026: pub=30/05/2026 → fy0=FY2026, ntm=0.940×FY2027+0.060×FY2028
FY mag 2026: pub=30/07/2026 > oggi → not_yet → eps_growth=FY2028/|FY2027|-1
FY giu 2026: pub=29/08/2026 > oggi → not_yet
FY set 2026: pub=29/11/2026 > oggi → not_yet

WEEKLY APAC — LOGICA CORRETTA (funzionante 21/06/2026)
File Colab: Untitled43.ipynb
CSV TIKR: /content/drive/MyDrive/ForwardAlpha/tikr_load_CAN_AP_200626 - Foglio1.csv.zip
STEP 1 — Leggi ticker da stocks (NON paginare prices_eod)

# CORRETTO — stocks è allineato con prices_eod
for exchange in ['TSE','SEHK','TSX','ASX']:
    offset = 0
    while True:
        r = req.get(SUPABASE_URL+"/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker","exchange":f"eq.{exchange}",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for d in batch: stocks_tickers[exchange].add(d['ticker'])
        offset += 1000
        if len(batch) < 1000: break

STEP 2 — Match TIKR con stocks (SEHK: lstrip zeros)

TARGETS = {'TSE':1000, 'SEHK':500, 'TSX':400, 'ASX':350}
if ex_tikr == 'SEHK':
    df['Ticker_match'] = df['Ticker'].astype(str).str.strip().str.lstrip('0')
else:
    df['Ticker_match'] = df['Ticker'].astype(str).str.strip()
df = df[df['Ticker_match'].apply(lambda t: t in stocks_tickers[exchange])]
df = df.nlargest(target, 'mktcap_num').head(target)





STEP 4 — Prezzi da prices_eod in chunk da 20

# CORRETTO — NON paginare tutta la tabella
CHUNK = 20
for i in range(0, len(tickers_needed), CHUNK):
    chunk = tickers_needed[i:i+CHUNK]
    ticker_filter = ','.join(chunk)
    offset = 0
    while True:
        r = req.get(SUPABASE_URL+"/rest/v1/prices_eod", headers=headers_r,
            params={"select":"ticker,date,adj_close",
                    "exchange":f"eq.{exchange}",
                    "ticker":f"in.({ticker_filter})",
                    "order":"ticker,date.desc",
                    "limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for d in batch:
            if d['adj_close'] is not None:
                all_ph[(d['ticker'],exchange)].append(
                    {'date':d['date'],'close':d['adj_close']})
        offset += 1000
        if len(batch) < 1000: break
    time.sleep(0.02)



Risultati 21/06/2026
JPN 1000: value 100%, growth 87%, combined 87%
HKG 500: value 99%, growth 80%, combined 80%
CAN 400: value 99%, growth 90%, combined None
AUS 350: value 97%, growth 87%, combined 87%
Prezzi verifica
Toyota 7203/TSE: ¥2776 ✓
Tencent 700/SEHK: HK$440 ✓
Royal Bank RY/TSX: C$284 ✓
BHP/ASX: A$61.4 ✓


FRONTEND — VALUTA PER EXCHANGE (page.tsx)

{['LSE','AIM'].includes(stock.exchange) ? 'p' :
 stock.exchange === 'SWX' ? 'CHF' :
 ['OM','NGM'].includes(stock.exchange) ? 'kr' :
 stock.exchange === 'OB' ? 'kr' :
 stock.exchange === 'CPSE' ? 'kr' :
 stock.exchange === 'US' ? 'USD' :
 stock.exchange === 'TSE' ? '¥' :
 stock.exchange === 'SEHK' ? 'HK$' :
 stock.exchange === 'TSX' ? 'C$' :
 stock.exchange === 'ASX' ? 'A$' :
 '€'}{fv(stock.price, 2)}

FRONTEND — PREZZO APAC (route.ts stocks)

price: ['TSE','SEHK','TSX','ASX'].includes(s.exchange)
  ? (f.price ?? null) // da fundamentals
  : (s.price ?? f.price ?? null), // da stocks poi fundamentals



RANK GROUPS
EU
ITA:MIL, DEU:XETRA, FRA:PA, GBR:LSE, SWE:OM, NOR:OB
CHE:SWX, NLD:AS, BEL:BR, FIN:HE, ESP:MC, DNK:CPSE, POR:LS
NO_RANK: VI, IR, NGM, AIM
APAC
JPN:TSE (1000), HKG:SEHK (500), CAN:TSX (400), AUS:ASX (350)
Combined AP: TSE+SEHK+ASX
US
in_universe=true, combined con CAN nel weekly_us
GITHUB ACTIONS
daily_eu.yml: cron 0 19 * * 1-5 (21:00 CET)
weekly_eu.yml: cron 0 7 * * 0 (domenica 09:00 CET)
weekly_us.yml: cron 0 7 * * 0
NOTA: GitHub API 403 per .github/workflows/ → modificare manualmente
STACK
Next.js 14, Vercel Pro, Supabase, GitHub Actions
Font: IBM Plex Sans, IBM Plex Mono, IBM Plex Sans Condensed
Colori: bg #0d1017, surface #111827, orange #f59e0b, green #22d48a, r
ed #e84560
FMP
Endpoint: /stable/p
rofile (NO
N /api/v3/profile — deprecato agosto 2025)
Suffissi: AS→.AS, BR→.BR, LS→.LS, OB→.OL, VI→.VI, IR→.IR
HE→.HE, CPSE→.CO, OM→.ST, MC→.MC, LSE→.L, AIM→.L
ISIN MANCANTI
AS: ERC, KORPT, OBAM, CABLE, BACE, LKFT, SWICH, TRIO
BR: ENRGY, NYXH, DEXB
LS: ALSMB, MLARR, MLATR, MLCIA, MLGSH, MLORE, MLVDN
OB: GENO, EISP, COSH, VIEI, SOMA, CAPT
VI: ATH, BMAG, EIOS, GHC, HRX5, HST, HUI, ICG, K2G, MWB, REGU, RWT, UKO, VAS, ZHT
IR: SENUS
HE: AUROORA, CANATU, CITYVA
Codice


---

## SESSIONE 27-28 GIUGNO 2026 — TUTTO QUELLO CHE È STATO FATTO

---

## LEEWAY — FUNZIONE leeway_ticker() DEFINITIVA

```python
SPECIAL_TICKERS = {
    "BP.": "BP.LSE", "RR.": "RR.LSE", "BT.A": "BT-A.LSE",
    "BA.": "BA.LSE", "NG.": "NG.LSE",
    "ROG": "RO.SW",  # Roche: ticker Leeway diverso da Bloomberg
}

LEEWAY_SUFFIX = {
    "MIL":  ".MI",    "XETRA": ".XETRA", "PA":   ".PA",
    "AS":   ".AS",    "MC":    ".MC",     "BR":   ".BR",
    "LS":   ".LS",    "VI":    ".VI",     "HE":   ".HE",
    "IR":   ".IR",    "AT":    ".VI",     # AT usa .VI non .AT
    "LSE":  ".LSE",   "AIM":   ".AIM",   "SWX":  ".SW",
    "OM":   ".ST",    "NGM":   ".ST",    "OB":   ".OL",
    "CPSE": ".CO",
    "US":   ".US",    "TSX":   ".TO",
    "TSE":  ".TSE",   "ASX":   ".AU",    # ASX usa .AU non .AX
}

def leeway_ticker(ticker, exchange):
    if ticker in SPECIAL_TICKERS: return SPECIAL_TICKERS[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"  # 700→0700.HK
    if exchange in ("CPSE", "OM", "NGM"): return ticker.replace(" ", "-") + LEEWAY_SUFFIX.get(exchange, "")
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"  # AD.UN→AD-UN.TO
    if exchange == "BR":  return ticker.replace(".", "") + ".BR"   # AGF.B→AGFB.BR
    ticker_clean = ticker.rstrip(".")  # UU.→UU (LSE ticker con punto finale)
    return ticker_clean + LEEWAY_SUFFIX.get(exchange, "")
```

### Regole confermate dai test (5238 titoli, OK=5238 VUOTI=0 a 2 req/sec)
- CPSE: spazio→trattino (AMBU B → AMBU-B.CO)
- OM/NGM: spazio→trattino (SCA B → SCA-B.ST)
- TSX: punto→trattino (AD.UN → AD-UN.TO, AGF.B → AGF-B.TO)
- BR: punto→nulla (AGF.B → AGFB.BR) — regola DIVERSA da TSX
- LSE: rstrip(".") dal ticker (UU. → UU.LSE, non UU..LSE)
- SEHK: zero-pad esatto 4 cifre (700→0700, 10→0010, mai 5 cifre)
- AT exchange: usa .VI non .AT (confermato 6/6 test)
- ASX: .AU non .AX (Array vuoto con .AX, OK con .AU)
- TSE: .TSE (es. 7203.TSE, 285A.TSE — alfanumerici supportati)
- STO3.XETRA: unico titolo non coperto da Leeway (ETF strutturato)
- Rate limit: 2 req/sec raccomandato da Lars (max tecnico 7 req/sec)
- Sleep nei daily: 0.5s tra ogni chiamata Leeway
- 100k chiamate/giorno incluse nel piano

---

## DAILY SCRIPTS — ARCHITETTURA DEFINITIVA

### Flusso identico per daily_eu.py, daily_apac.py, daily_us.py

```
Step 1: Carica universo da stocks (in_universe=true)
        - Leggi anche yahoo_ticker per fallback
Step 2: Scarica prezzi EOD da Leeway → salva in prices_eod
        - sleep 0.5s tra chiamate
        - Se last_date >= TODAY → skip (già aggiornato)
        - start_dt = last_date + 1 giorno
Step 3: Leggi prezzi da prices_eod
        - Chunk da 20 ticker
        - Filtro date >= oggi-400 giorni (evita che un ticker monopolizzi 1000 righe)
        - Ordine: ticker, date.desc
        - Risultato: all_ph = {(ticker, exchange): [{"date":..., "close":...}]}
Step 4: Calcola momentum da all_ph (prezzi NUOVI)
        - mom1w: closest a 7 giorni fa
        - mom1m: closest a 31 giorni fa
        - mom6m: closest a 182 giorni fa
        - mom12m: closest a 365 giorni fa
        - change1d: data[0]/data[1] - 1
        - Risultato: mom_updates = lista dizionari
Step 5: POST mom_updates a fundamentals (upsert)
Step 6 (solo EU): Aggiorna FX rates via yfinance
Step 7: Leggi all_data da fundamentals
        - Campi: pe_trailing, pe_forward, pb, eps_growth, rev_growth, mom6m, mom12m, mom1w, mom1m
Step 8: Costruisci mappe momentum da mom_updates (NON da all_data/DB vecchio)
        mom1w_map  = {(ticker, exchange): mom1w  for d in mom_updates}
        mom1m_map  = {(ticker, exchange): mom1m  for d in mom_updates}
        mom6m_map  = {(ticker, exchange): mom6m  for d in mom_updates}
        mom12m_map = {(ticker, exchange): mom12m for d in mom_updates}
        Fallback: d.get("mom6m") da fundamentals se titolo non in mom_updates
Step 9: Calcola rank per paese (RANK_GROUPS)
        - value_score: r_eyt, r_eyf, r_pb (min 2/3)
        - growth_score: r_epsg, r_revg, r_m6, r_m12 (min 3/4)
        - mom6m_adj = mom6m - mom1w (aggiustato overbought)
        - mom12m_adj = mom12m - mom1m
Step 10: Calcola combined rank (EU o AP o US)
Step 11: Aggiorna indici
Step 12: Salva log in daily_log
```

### Schedule GitHub Actions
- daily_eu.py: `0 19 * * 1-5` (21:00 CET) — exchange not.in.(US,TSX,TSE,SEHK,ASX)
- daily_apac.py: `0 20 * * 1-5` (22:00 CET) — exchange in.(TSE,SEHK,ASX)
- daily_us.py: exchange in.(US,TSX)

### RANK_GROUPS
```python
# EU
RANK_GROUPS = {
    "ITA": ["MIL"], "DEU": ["XETRA"], "FRA": ["PA"], "GBR": ["LSE"],
    "SWE": ["OM"],  "NOR": ["OB"],    "CHE": ["SWX"], "NLD": ["AS"],
    "BEL": ["BR"],  "FIN": ["HE"],    "ESP": ["MC"],  "DNK": ["CPSE"],
    "POR": ["LS"],
}
NO_RANK = {"AT", "VI", "IR", "NGM", "AIM"}

# APAC
RANK_GROUPS = {
    "JPN": ["TSE"], "HKG": ["SEHK"], "AUS": ["ASX"],
}
# Combined AP = TSE+SEHK+ASX insieme
# TSX (Canada) non ha combined APAC — calcolato con US nel weekly_us

# US: tutti insieme, combined con TSX nel weekly_us
```

---

## INDICI — TICKER LEEWAY CONFERMATI

### EU (da aggiornare in daily_eu.py → EU_INDICES)
```python
EU_INDICES = [
    ("GDAXI.INDX",   "XETRA", "DAX",    "DAX"),           # 24.994 ✅
    ("FCHI.INDX",    "PA",    "FCHI",   "CAC 40"),         # 8.431 ✅
    ("AEX.INDX",     "AS",    "AEX",    "AEX"),            # 1.067 ✅
    ("IBEX.INDX",    "MC",    "IBEX",   "IBEX 35"),        # 19.425 ✅
    ("BFX.INDX",     "BR",    "BFX",    "BEL 20"),         # 5.739 ✅
    ("SSMI.INDX",    "SWX",   "SMI",    "SMI"),            # 14.231 ✅
    ("ATX.INDX",     "VI",    "ATX",    "ATX"),            # 6.488 ✅
    ("OMXS30.INDX",  "OM",    "OMXS30", "OMX Stockholm"),  # 3.153 ✅
    ("OMXC25.INDX",  "CPSE",  "C25",    "OMX Copenhagen"), # 1.800 ✅
    ("OMXH25.INDX",  "HE",    "HEX",    "OMX Helsinki"),   # 6.143 ✅  (non OMXHPI)
    ("STOXX50E.INDX","EZ",    "SX5E",   "Euro Stoxx 50"),  # 6.267 ✅
    ("SXXP.INDX",    "EZ",    "SXXP",   "STOXX 600"),      # 635 ✅
    ("PSI20.INDX",   "LS",    "PSI",    "PSI 20"),         # 9.136 ✅
    # NON DISPONIBILI SU LEEWAY:
    # FTSEMIB.MI → FTSE MIB (da chiedere a Lars)
    # FTSE.INDX  → FTSE 100 (da chiedere a Lars)
    # ISEQ.INDX  → ISEQ (da chiedere a Lars)
]
```

### NA (daily_us.py → NA_INDICES)
```python
NA_INDICES = [
    ("GSPC.INDX",   "US",  "GSPC",  "S&P 500"),   # 7.367 ✅
    ("IXIC.INDX",   "US",  "IXIC",  "Nasdaq"),    # 25.371 ✅
    ("DJI.INDX",    "US",  "DJI",   "Dow Jones"), # 51.927 ✅
    ("GSPTSE.INDX", "TSX", "GSPTSE","TSX"),        # 34.909 ✅ (non OSPTSX)
]
```

### APAC (daily_apac.py → APAC_INDICES)
```python
APAC_INDICES = [
    ("N225.INDX", "TSE",  "N225", "Nikkei 225"),
    ("HSI.INDX",  "SEHK", "HSI",  "Hang Seng"),
    ("AXJO.INDX", "ASX",  "AXJO", "ASX 200"),
]
```

### Regole indici
- USA SEMPRE `close` (non `adjusted_close`) — adjusted_close per indici è sbagliato
- Ordina dati per data ASC prima di prendere last/prev
- Filtra close > 0 per evitare righe corrotte
- Scarica 12 mesi di storia
- Salva in tabella `indices` (non price_history)
- PATCH con ticker come chiave

---

## NEWS PAGE — ARCHITETTURA

### Report nella News Page
- **Best Score Report**: ordina per bestScore (combined_rank) DESC, ultime 24h, max 1 per ticker, top 10 per regione
- **Market Cap Report**: ordina per mktCap DESC, ultime 24h, max 1 per ticker, top 10 per regione

### MarketStrip
- Link Yahoo Finance cliccabili per indici (Americas, Europe, Asia Pac)
- TradingView widget per commodities e FX (Gold, Oil WTI, EUR/USD, USD/JPY, GBP/USD)
- NON mostrare prezzi live degli indici — solo link Yahoo

### API /api/ticker-news
- Legge da fundamentals ordinato per mkt_cap DESC
- Restituisce: ticker, exchange, company, yahooTicker, valueScore, growthScore, bestScore, mktCap

---

## FETCH NEWS CACHE

### fetch_news_cache.py
- Top 200 US+CA + top 50 EU + top 50 Asia ogni ora
- Restanti (~4200 titoli) ogni 3 ore (shell: HOUR%3==0)
- ThreadPoolExecutor 20 worker per parallelismo
- Salva in tabella `news_cache` Supabase

### Workflow fetch_news_cache.yml
```yaml
schedule:
  - cron: '0 * * * *'  # ogni ora
# Logic shell:
# HOUR=$(date -u +%H)
# if [ $((HOUR % 3)) -eq 0 ]; then
#   python fetch_news_cache.py all  # tutti i ticker
# else
#   python fetch_news_cache.py      # solo top
```

---

## SEO (aggiornamenti giugno 2026)

### layout.tsx
```typescript
title: 'ForwardAlpha — Global Equity Research | 7,000+ Stocks Ranked',
description: 'Institutional-grade Value & Growth scoring across 7,000+ global stocks: Europe, US, Canada, Japan, Hong Kong, Australia. Daily price refresh. Built by ex J.P. Morgan & Zenit SGR Portfolio Manager, CFA.',
```

### sitemap.ts (src/app/sitemap.ts)
- Include TUTTE le borse: EU + US + TSX + TSE + SEHK + ASX
- Top 50 titoli per mktCap con priority 0.9 (Nvidia, ASML, Tencent appaiono per primi nei sitelink Google)
- Pagine statiche: /, /news, /screens, /screens/europe, /screens/us, /screens/asia, /research, /about, /legal
- NB: la sitemap è DINAMICA (src/app/sitemap.ts) — non creare public/sitemap.xml statica
- Google Search Console: 5243 pagine rilevate, sitemap inviata il 29/05/2026

### JSON-LD in homepage (page.tsx)
```typescript
const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'ForwardAlpha',
  url: 'https://forwardalpha.pro',
  ...
}
```

---

## UNIVERSO AGGIORNATO (giugno 2026)

| Exchange | Titoli in_universe | Mercato |
|----------|-------------------|---------|
| US       | 1.967             | NYSE/NASDAQ |
| TSE      | 1.000             | Tokyo |
| SEHK     | 500               | Hong Kong |
| TSX      | 387               | Toronto |
| LSE      | 375               | Londra |
| ASX      | 350               | Australia |
| PA       | 200               | Parigi |
| XETRA    | 186               | Francoforte |
| OM       | 184               | Stoccolma |
| SWX      | 142               | Zurigo |
| MIL      | 109               | Milano |
| AS       | 100               | Amsterdam |
| HE       | 100               | Helsinki |
| BR       | 99                | Bruxelles |
| CPSE     | 98                | Copenhagen |
| OB       | 98                | Oslo |
| MC       | 88                | Madrid |
| VI       | 70                | Vienna |
| LS       | 39                | Lisbona |
| IR       | 16                | Dublino |
| **TOTALE** | **6.108**       | |

EU totale: 1.904 | US: 1.967 | TSX: 387 | APAC: 1.850

---

## PROBLEMI RISOLTI IN QUESTA SESSIONE

1. **Suffisso ASX sbagliato**: .AX → .AU (prezzi fermi al 19 giugno)
2. **Suffisso AT sbagliato**: .AT → .VI
3. **Doppio punto LSE**: UU. → rstrip(".") → UU.LSE
4. **Spazio in ticker OM/CPSE**: spazio → trattino
5. **Punto in ticker TSX**: punto → trattino (AD.UN → AD-UN.TO)
6. **Punto in ticker BR**: punto → nulla (AGF.B → AGFB.BR)
7. **Roche su SWX**: ROG → RO.SW (ticker Bloomberg ≠ Leeway)
8. **Rate limit Leeway**: troppi thread → falsi vuoti. Fix: 2 req/sec, loop sequenziale
9. **Indici valore sbagliato**: adjusted_close → close per indici
10. **Indici invertiti (±17.4%)**: dati non ordinati per data → fix sorted(data, key=date) ASC
11. **FTSE MIB 53 invece di 53.000**: non disponibile su Leeway (in attesa da Lars)
12. **Helsinki indice**: OMXHPI.INDX vuoto → OMXH25.INDX ✅
13. **TSX indice**: OSPTSX.INDX vuoto → GSPTSE.INDX ✅
14. **Growth score non cambia**: filtro 400 giorni su prices_eod evita che un ticker monopolizzi le 1000 righe del chunk
15. **daily_apac troncato**: file riscritto da zero dopo corruzione
16. **f-string con doppie graffe**: riscritti i daily senza f-string per le query Supabase
17. **combined_rank EU**: calcolato su tutti i paesi EU insieme (non per paese)
18. **News Page generateReportBest**: ripristinato dal commit ad4cb211 (funzionante)
19. **Market Cap Report**: aggiunto secondo report che ordina per mktCap reale
20. **Link cliccabili nella News**: renderLines() con link "📰 Read article" e "📊 View on ForwardAlpha"
21. **Cache 30 min**: /api/yahoo-news e /api/ticker-news con cache-control
22. **sitemap.xml duplicata**: eliminata public/sitemap.xml (esiste già src/app/sitemap.ts dinamica)

---

## PENDENTI / DA FARE

1. **FTSE MIB e FTSE 100**: chiedere a Lars il ticker corretto su Leeway
2. **ISEQ**: ticker Leeway da verificare
3. **Dashboard APAC**: pagina non ancora creata (indici pronti in Supabase)
4. **Growth/best score che non cambia**: verificare dopo il prossimo run daily con il fix filtro 400 giorni
5. **Vercel build**: verificare dopo ogni modifica
6. **Google Search Console**: richiedere reindicizzazione homepage dopo fix title

## PROSSIMA SESSIONE — REBUILD UNIVERSI

### TIKR già scaricati
- EU + NA (US+CA): pronti da processare
- APAC: da scaricare, aggiungere +500 Corea (KRX)

### Universi target
| Mercato | Exchange | Titoli target |
|---------|----------|---------------|
| Europa  | MIL/XETRA/PA/LSE/OM/SWX/OB/AS/MC/BR/CPSE/HE/VI/IR/LS | ~2.100 |
| US      | US       | ~2.000 |
| Canada  | TSX      | ~400 |
| Giappone| TSE      | ~1.000 |
| Hong Kong| SEHK    | ~500 |
| Australia| ASX     | ~350 |
| Corea   | KRX      | ~350-400 |
| Singapore | SGX    | ~100 |

### Da fare
1. Applicare filtri esclusione (fondi, ETF, settori 71-77) a EU e US come già fatto per APAC
2. Aggiungere KRX (Corea) — verificare suffix Leeway con Lars, rimuovere "A" iniziale dai ticker numerici
3. Aggiungere SGX (Singapore) — ~200 titoli TIKR, universo top 100 per mktcap
4. Combined rank Nord America = US + TSX insieme (come AP = TSE+SEHK+ASX)
   - Aggiornare weekly_us per calcolare combined NA su distribuzione unica US+TSX
   - Screen Nord America aggregato nel frontend
5. Nuovo screen Corea nel frontend (~350-400 titoli)
6. Nuovo screen Singapore nel frontend (~100 titoli)
7. Screen Asia Pacific aggiornato: JP+HK+AU+KR+SG
8. Modificare daily_apac per includere KRX e SGX nei prezzi e momentum
9. Modificare weekly per includere KRX e SGX nei rank

---

## TEST LEEWAY (test_leeway_indices.py)

### Script di test
- Loop sequenziale, sleep 0.5s, timeout 15s per chiamata
- Testa tutti i 6108 titoli in universe
- Risultato definitivo: OK=5238/5238 VUOTI=0 (solo borse EU+US+CA+APAC, escluso MIL/XETRA/PA/LSE già verificati separatamente)
- Workflow: .github/workflows/test_leeway.yml (no timeout)

---

## GITHUB ACTIONS — WORKFLOWS ATTIVI

| Workflow | Schedule | Note |
|----------|----------|------|
| daily_eu.yml | `0 19 * * 1-5` | 21:00 CET |
| daily_apac.yml | `0 20 * * 1-5` | 22:00 CET |
| daily_us.yml | separato | |
| fetch_news_cache.yml | `0 * * * *` | ogni ora, HOUR%3 per full |
| test_leeway.yml | manuale | no timeout |
| fix_combined_rank.yml | manuale | |


---

## CALENDARIZZAZIONE — PROBLEMA ANNO 2026→2027

### Problema hardcoding anni
La formula attuale ha gli anni hardcodati:
```python
if fy_end.year >= 2026:
    v0, v1, v2 = fy2026, fy2027, fy2028
else:
    v0, v1, v2 = fy2025, fy2026, fy2027
```
Quando arriviamo a fine 2026, la colonna `fiscal_year_end` nel DB passerà da
`2025-12-31` a `2026-12-31` — e la formula punterebbe ancora a FY2026/FY2027/FY2028
invece di FY2027/FY2028/FY2029.

### Da verificare prima di fine 2026
1. **Colonna `fiscal_year_end` nel DB**: contiene date come `2025-12-31` o `2026-12-31`?
   - Se contiene l'anno esplicito → si aggiorna automaticamente con il nuovo TIKR
   - Se contiene solo mese/giorno → non cambia e va aggiornato manualmente
2. **Nuovo TIKR da scaricare**: deve includere FY2027, FY2028, FY2029
3. **Formula da rendere dinamica** basata su `datetime.now().year` invece di hardcoding 2025/2026

### Soluzione proposta (da implementare a fine 2026)
```python
CURRENT_YEAR = datetime.now().year
if fy_end.year >= CURRENT_YEAR:
    v0 = fundamentals[f"fy{CURRENT_YEAR}"]
    v1 = fundamentals[f"fy{CURRENT_YEAR+1}"]
    v2 = fundamentals[f"fy{CURRENT_YEAR+2}"]
else:
    v0 = fundamentals[f"fy{CURRENT_YEAR-1}"]
    v1 = fundamentals[f"fy{CURRENT_YEAR}"]
    v2 = fundamentals[f"fy{CURRENT_YEAR+1}"]
```
Questo richiede che le colonne in Supabase si chiamino `fy2025`, `fy2026` ecc.
e che vengano aggiunte `fy2027`, `fy2028`, `fy2029` con il prossimo TIKR.

### India
- Lars conferma copertura Leeway ma fondamentali probabilmente incompleti
- Verificare con Lars copertura EPS estimates per NSE prima di integrare
- Se integrata: exchange = NSE, suffix Leeway da confermare


---

## NUOVO TIKR — EPS/REVENUE FY2028/FY2029/FY2030

### Dati disponibili nel nuovo TIKR (scaricato giugno 2026)
- EU + NA (US+CA): già scaricati
- APAC + Corea (KRX): da scaricare
- Colonne EPS e Revenue: FY2026, FY2027, FY2028, FY2029, FY2030

### Nuovi calcoli da implementare

**1. EPS Growth 3 anni (consensus)**
```python
eps_cagr_3y = (eps_fy2029 / abs(eps_ntm)) ** (1/3) - 1
# oppure da FY2027 a FY2030
eps_cagr_3y = (eps_fy2030 / abs(eps_fy2027)) ** (1/3) - 1
```

**2. Reverse DCF — EPS growth implicito nel prezzo**
```python
# Ke = Risk Free Rate + Beta * ERP (CAPM)
# Beta da Leeway (5 anni vs S&P500)
# Risk Free = rendimento BTP 10Y o Treasury 10Y
# ERP = 5% (assumption standard)
Ke = rf + beta * erp

# Gordon Growth Model inverso:
# Prezzo = EPS_NTM / (Ke - g)  →  g = Ke - EPS_NTM/Prezzo
implied_growth = Ke - (eps_ntm / price)

# Confronto:
# Se consensus_cagr_3y > implied_growth → titolo potenzialmente sottovalutato
# Se consensus_cagr_3y < implied_growth → potenzialmente sopravvalutato
```

**3. Aggiunta al Growth Score o scheda titolo**
- Mostrare `implied_growth` vs `eps_cagr_3y` sulla stock page
- Possibile nuovo parametro nel rank: titoli dove consensus > implied

### Colonne da aggiungere a Supabase (fundamentals)
- `eps_fy2028`, `eps_fy2029`, `eps_fy2030`
- `rev_fy2028`, `rev_fy2029`, `rev_fy2030`
- `eps_cagr_3y` (calcolato dal weekly)
- `implied_growth` (calcolato dal daily con prezzi aggiornati)
- `beta` (da Leeway — già disponibile nel /fundamentals endpoint)

### Calendarizzazione aggiornata
Con FY2030 disponibile, gli anni fissi diventano:
- fy0=FY2026, fy1=FY2027, fy2=FY2028, fy3=FY2029, fy4=FY2030
- eps_ntm calcolato come prima (blend fy1/fy2)
- eps_cagr_3y = CAGR da eps_ntm a fy4 (3 anni forward)


---

## BUG CRITICO — GROWTH/BEST SCORE NON CAMBIA (DA VERIFICARE)

### Stato al 28 giugno 2026
Fix applicati ma NON ancora verificati in produzione:
1. Filtro 400 giorni su prices_eod (chunk da 20 ticker)
2. Mappe momentum costruite da mom_updates (non da DB vecchio)

### Come verificare al prossimo run
1. Prima del daily: annota growth_score di 5 titoli EU (es. ENI, SAP, LVMH, ASML, NESN)
2. Lancia daily_eu
3. Dopo il run: confronta growth_score — devono essere cambiati

### Se ancora non cambiano — debug da fare
Aggiungere print nel daily per verificare:
```python
print(f"mom_updates: {len(mom_updates)} titoli")
print(f"all_ph: {len(all_ph)} titoli")
print(f"all_data: {len(all_data)} titoli")
# Campione: stampa momentum di 3 titoli noti
for ticker, exchange in [("ENI","MIL"),("SAP","XETRA"),("MC","PA")]:
    key = (ticker, exchange)
    print(f"{ticker}: mom6m_map={mom6m_map.get(key)} mom12m_map={mom12m_map.get(key)}")
    fund = next((d for d in all_data if d["ticker"]==ticker), None)
    if fund: print(f"  DB mom6m={fund.get('mom6m')} mom12m={fund.get('mom12m')}")
```

### Causa più probabile se il bug persiste
Il POST di mom_updates a fundamentals usa upsert ma la chiave
primaria potrebbe non corrispondere — verificare che il PATCH/POST
aggiorni effettivamente i record esistenti e non crei duplicati.


---

## REVERSE DCF — IMPLEMENTAZIONE COMPLETA

### Filosofia (Expectations Investing — Mauboussin)
Non indovinare il prezzo futuro. Partire dal prezzo attuale per capire quali
aspettative incorpora, poi decidere se quelle aspettative sono troppo
pessimistiche o ottimistiche.

### Modello a due stadi
- **Stage 1**: crescita g implicita per 10 anni (incognita da trovare)
- **Stage 2**: crescita terminale gTV = 2.5% dal decimo anno in poi (fissata)

### Input del modello
- **EPS_NTM**: utile per azione next twelve months (calendarizzato da TIKR)
  - Se EPS_NTM < 0 → fallback su EPS_LTM
  - Se anche EPS_LTM < 0 → modello non applicabile (mostra N/A)
- **Prezzo**: ultimo prezzo da Leeway (in valuta locale)
- **Ke**: costo del capitale = Rf + Beta × ERP
- **Beta**: calcolato da noi su 5 anni mensili vs indice locale (NON Beta Leeway)
- **Rf**: rendimento decennale del mercato di riferimento
- **ERP**: 5.0% (standard globale)
- **gTV**: 2.5% (crescita terminale perpetua)
- **Giappone TSE**: ESCLUSO — EPS GAAP non comparabile con EPS normalized

### Indici di riferimento per Beta locale
```
MIL → FTSE MIB (FTSEMIB.MI)
XETRA → DAX (GDAXI.INDX)
PA → CAC 40 (FCHI.INDX)
LSE → FTSE 100 (FTSE.INDX)
US → S&P 500 (GSPC.INDX)
TSX → S&P/TSX (GSPTSE.INDX)
SEHK → Hang Seng (HSI.INDX)
ASX → ASX 200 (AXJO.INDX)
OM → OMX Stockholm (OMXS30.INDX)
OB → OB All-Share (OB.INDX)
CPSE → OMX Copenhagen (OMXC25.INDX)
HE → OMX Helsinki (OMXH25.INDX)
SWX → SMI (SSMI.INDX)
MC → IBEX 35 (IBEX.INDX)
AS → AEX (AEX.INDX)
KRX → KOSPI
SGX → STI
```

### Risk-free rate per mercato (da aggiornare mensilmente)
```
US, CA, HK → Treasury 10Y USA
EU (€) → Bund 10Y (Germania)
ITA → BTP 10Y (spread paese)
UK → Gilt 10Y
CHE → Swiss Gov 10Y
SWE → Swedish Gov 10Y
NOR → Norwegian Gov 10Y
DNK → Danish Gov 10Y
AUS → ACGB 10Y
KOR → KTB 10Y
SGP → SGS 10Y
JPN → JGB 10Y (~0.8%) — ma TSE escluso dal modello
```
Fonte: FMP /stable/treasury o aggiornamento manuale mensile.

### Algoritmo Reverse DCF (bisection method — Python)
```python
def reverse_dcf(price, eps_ntm, ke, g_tv=0.025, years=10, tol=1e-6):
    """
    Trova il tasso di crescita g implicito nel prezzo corrente.
    Usa il metodo della bisezione.
    """
    def dcf_price(g):
        pv = 0
        eps = eps_ntm
        for t in range(1, years + 1):
            if t > 1:
                eps = eps * (1 + g)
            pv += eps / (1 + ke) ** t
        # Terminal Value
        tv = (eps * (1 + g_tv)) / (ke - g_tv)
        pv += tv / (1 + ke) ** years
        return pv

    # Bisezione tra -50% e +100%
    lo, hi = -0.50, 1.00
    for _ in range(100):
        mid = (lo + hi) / 2
        if dcf_price(mid) > price:
            hi = mid
        else:
            lo = mid
        if (hi - lo) < tol:
            break
    return round((lo + hi) / 2 * 100, 2)  # restituisce % con 2 decimali
```

### Forward DCF (calcola Fair Value dalla stima utente — JavaScript)
```javascript
function calculateUserFairValue(epsNtm, userGrowthRate, ke, terminalGrowthRate = 0.025) {
    let presentValue = 0;
    let currentEps = epsNtm;

    for (let t = 1; t <= 10; t++) {
        if (t > 1) currentEps = currentEps * (1 + userGrowthRate);
        presentValue += currentEps / Math.pow(1 + ke, t);
    }

    const terminalValue = (currentEps * (1 + terminalGrowthRate)) / (ke - terminalGrowthRate);
    const discountedTV = terminalValue / Math.pow(1 + ke, 10);

    return Math.round((presentValue + discountedTV) * 100) / 100;
}
```

### UX sulla stock page
**Layout a tre blocchi:**

1. **Dato di mercato (passivo)**
   - Prezzo attuale: X €
   - Tasso di crescita implicito: **8,4%** annuo per 10 anni
   - *(assumendo gTV=2.5%, Ke=9.2%, Beta=0.85)*
   - Consensus analisti FY+1/FY+2: **+12%** annuo

2. **Input utente (attivo)**
   - Slider o campo: "La tua stima di crescita decennale: [ ___ % ]"

3. **Output dinamico (feedback immediato)**
   - "Con una crescita del X%, il modello calcola un valore teorico di Y €"
   - Divergenza vs prezzo attuale: +Z% / -Z%

### Copywriting (no investment advice)
```
"Per giustificare l'attuale prezzo di borsa, il modello matematico implica
che gli utili debbano crescere in media dell'8,4% annuo per i prossimi
10 anni (crescita terminale 2,5% dal decimo anno).

Il consensus degli analisti stima una crescita media del 12% per i
prossimi 2 anni.

Inserisci la tua stima decennale per calcolare il valore teorico secondo
il modello."
```

### Disclaimer obbligatorio
```
"I dati e i modelli presentati hanno scopo puramente informativo ed
educativo. I risultati del Reverse Model sono frutto di calcoli matematici
basati su dati pubblici e non costituiscono sollecitazione al pubblico
risparmio o consulenza in materia di investimenti ai sensi del D.Lgs.
58/1998 (TUF) e della Direttiva MiFID II. Ogni decisione operativa è
sotto la completa ed esclusiva responsabilità dell'utente."
```

### Verbi da usare (no investment advice)
- ✅ "Il modello calcola", "La formula implica", "Il mercato prezza"
- ✅ "Valore teorico superiore/inferiore al prezzo attuale"
- ✅ "Divergenza positiva/negativa"
- ❌ "Sottovalutato/Sopravvalutato"
- ❌ "Compra/Vendi"
- ❌ "Il titolo è conveniente"

### Colonne da aggiungere a Supabase (fundamentals)
- `implied_growth` (calcolato dal daily con prezzi Leeway aggiornati)
- `ke` (costo del capitale, calcolato dal weekly con beta locale)
- `beta_local` (calcolato da noi su 5 anni mensili vs indice locale)
- `rf_rate` (risk-free del mercato, aggiornato mensilmente)
- `eps_cagr_3y` (CAGR consensus FY+1 → FY+3 da TIKR)

### Priorità implementazione
1. Calcolo beta locale (prezzi indici già in Supabase)
2. Raccolta Rf rates per mercato (FMP o manuale)
3. Script Python reverse_dcf() nel weekly
4. Componente React interattivo sulla stock page
5. Disclaimer nella pagina /legal


---

## BACK NAVIGATION — SOLUZIONE DEFINITIVA (giugno 2026)

### Problema
Next.js 14 App Router usa una Router Cache aggressiva. Quando navighi da una pagina a `/stock/[id]` e torni indietro, il componente precedente può essere ripristinato dalla cache senza rimontarsi — causando spinner infiniti o stato congelato.

### Soluzione per tipo di pagina

**1. Homepage SPA (`/` con `?page=...`)**
- La homepage NON usa `useState<Page>` — deriva `page` direttamente da `searchParams`
- `const page = (searchParams.get('page') as Page) ?? 'dashboard'`
- Per cambiare schermata: `router.replace('/?page=netherlands', { scroll: false })`
- Quando si torna da `/stock/[id]` con `router.push('/?page=netherlands')`, la homepage legge l'URL e mostra automaticamente la schermata corretta
- Il componente è wrappato in `<Suspense>` obbligatorio per `useSearchParams()`

**2. Pagine con fetch pesanti al mount (`/news`)**
- Usare `<a href>` nativo nei link ai titoli — NON `<Link>` di Next.js
- Il Back usa `window.history.back()` — NON `router.push()` o `router.back()`
- Motivo: `<a href>` fa hard navigation, il browser ricarica `/news` da zero al ritorno
- `router.push('/news')` lascia il componente in cache congelato → spinner infinito
- `router.refresh()` dopo `router.push()` causa freeze fatale in Next.js 14 — MAI usarli insieme

**3. Pagine research (`/research/[slug]`)**
- Usare `<Link href>` di Next.js nei link ai titoli
- Il Back usa `router.back()` — funziona nativamente

### Codice bottone Back in `/stock/[id]/page.tsx`
```typescript
const handleBack = () => {
  const from = searchParams.get('from')
  if (from) {
    const decoded = decodeURIComponent(from)
    // Per /news usa history.back() — evita freeze da Router Cache
    if (decoded === '/news') {
      window.history.back()
    } else {
      router.push(decoded)  // Per homepage SPA e altre pagine
    }
  } else {
    window.history.back()
  }
}
```

### Codice link in NewsPage.tsx
```typescript
// USA <a href> NATIVO — non <Link> di Next.js
<a href={'/stock/' + item.ticker + '-' + item.exchange}
   style={{ ... }}>
  {item.ticker} ↗
</a>
```

### Codice homepage (page.tsx)
```typescript
// UNICA SORGENTE DI VERITA' — nessun useState per page
const searchParams = useSearchParams()
const page = (searchParams.get('page') as Page) ?? 'dashboard'

const navigateTo = (newPage: Page) => {
  if (newPage === 'dashboard') {
    appRouter.replace('/', { scroll: false })
  } else {
    appRouter.replace(`/?page=${newPage}`, { scroll: false })
  }
}
```

### Regola generale
| Tipo pagina | Link a stock | Back |
|-------------|-------------|------|
| Homepage SPA (`/?page=...`) | `router.push` con `?from=` | `router.push(from)` |
| News (`/news`) | `<a href>` nativo | `window.history.back()` |
| Research (`/research/...`) | `<Link href>` Next.js | `router.back()` |
| MyScreen (dentro homepage) | `router.push` con `?from=` | `router.push(from)` |

### Causa root
Next.js 14 Router Cache non smonta i Client Components — li nasconde in memoria.
`useEffect([], ...)` non scatta al ritorno dalla cache.
L'unico modo sicuro per pagine con fetch pesanti è la navigazione nativa del browser.
