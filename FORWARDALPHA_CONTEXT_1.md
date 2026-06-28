
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









