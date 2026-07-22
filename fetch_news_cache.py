#!/usr/bin/env python3
# FORWARDALPHA — FETCH NEWS CACHE
# Scarica notizie per top ticker, con rotazione intelligente basata
# sugli orari reali dei mercati (segue il flusso informativo vero,
# non processa alla cieca tutto l'universo ogni volta).

import os, json, requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

NOW   = datetime.now().isoformat()
AGO24 = (datetime.now() - timedelta(hours=24)).isoformat()

STOP = {'Inc','Ltd','Corp','Group','SA','AG','NV','PLC','SE','Co',
    'The','Holdings','International','Global','Company','Corporation','Limited',
    'de','et','und','of','and'}

YAHOO_SUFFIX = {
    'PA':'.PA','XETRA':'.DE','MIL':'.MI','MC':'.MC','AS':'.AS',
    'BR':'.BR','LSE':'.L','SWX':'.SW','OM':'.ST','OB':'.OL',
    'HE':'.HE','IR':'.IR','VI':'.VI','CPSE':'.CO',
    'TSE':'.T','SEHK':'.HK','ASX':'.AX','TSX':'.TO','US':''
}

REGIONS = {
    'americas': ['US','TSX'],
    'europe':   ['PA','XETRA','MIL','MC','AS','BR','LSE','SWX','OM','OB','HE','IR','VI','CPSE'],
    'asia':     ['TSE','SEHK','ASX','KRX','SGX'],
}

# Finestre di attivita' informativa reale, ora italiana (Europe/Rome).
# Fuori da queste finestre un mercato non pubblica notizie fresche,
# quindi non ha senso processarlo — si segue il flusso informativo vero
# invece di girare alla cieca su tutto l'universo ogni volta.
MARKET_WINDOWS = {
    'asia':     (2, 10),   # 02:00-10:00, nessuna sovrapposizione con Europa
    'europe':   (10, 18),  # 10:00-18:00
    'americas': (12, 23),  # 12:00-23:00 (pre-market da mezzogiorno) — si
                            # sovrappone a Europa solo tra le 12:00 e le 18:00
}

def active_regions_now():
    rome_now = datetime.now(ZoneInfo("Europe/Rome"))
    hour = rome_now.hour
    active = [r for r, (start, end) in MARKET_WINDOWS.items() if start <= hour < end]
    return active or list(REGIONS.keys())  # fallback: se fuori da tutte le finestre, copre tutto piano piano

CHUNK_SIZE = 2000
STATE_FILE = "news_rotation_state.json"

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"active_regions": [], "index": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

import sys

import xml.etree.ElementTree as ET

def parse_rss(xml_text):
    items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.findall('.//item'):
            title  = (item.findtext('title') or '').strip()
            link   = (item.findtext('link') or '').strip()
            pubdate= (item.findtext('pubDate') or '').strip()
            source = (item.findtext('source') or 'Yahoo Finance').strip()
            if title and len(title) > 10:
                items.append({'title':title,'link':link,'pubDate':pubdate,'source':source})
    except: pass
    return items[:10]

def fetch_ticker_news(ticker, exchange, company, yahoo_ticker):
    results = []
    UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    # Solo Google News RSS — aggrega gia' articoli di Yahoo Finance e altre
    # fonti, osservato empiricamente (pagina titolo singolo usa solo Google
    # come fonte dichiarata ma mostra spesso articoli originati da Yahoo).
    # Rimossa la chiamata diretta a Yahoo: dimezza il carico totale di
    # richieste esterne, riducendo rischio di timeout/blocco.
    name_words = [w for w in company.split() if len(w)>2 and w not in STOP][:2]
    if name_words:
        try:
            is_us = exchange in ['US','TSX']
            query = ' '.join(name_words) + (' ' + yahoo_ticker.split('.')[0] if is_us else '') + ' stock'
            gl = 'US' if is_us else 'GB'
            url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en&gl={gl}&ceid={gl}:en"
            r = requests.get(url, headers={'User-Agent': UA}, timeout=8)
            if r.status_code == 200:
                results.extend(parse_rss(r.text))
        except: pass
    # Deduplica
    seen = set()
    deduped = []
    for item in results:
        k = item['title'][:50].lower()
        if k not in seen:
            seen.add(k)
            deduped.append(item)
    return deduped[:5]

print("=" * 60)
print(f"FETCH NEWS CACHE — {NOW}")
print("=" * 60)

# Pulisci notizie vecchie (solo quelle davvero vecchie, non tocca i
# gruppi appena inseriti da esecuzioni precedenti della rotazione)
requests.delete(SUPABASE_URL + "/rest/v1/news_cache",
    headers={**headers_r, "Content-Type": "application/json"},
    params={"fetched_at": f"lt.{AGO24}"})
print("Notizie vecchie eliminate")

# Determina le regioni attive ORA, in base agli orari reali dei mercati
active = active_regions_now()
print(f"\nRegioni attive ora (Europe/Rome): {active}")

# Costruisce il pool UNIFICATO di titoli dalle sole regioni attive —
# non l'intero universo alla cieca, solo dove c'e' davvero flusso
# informativo in questo momento.
in_universe = {}   # key: (ticker,exchange) -> stock info + region
funds_map = {}      # key: (ticker,exchange) -> fundamentals
for region in active:
    exchanges = REGIONS[region]
    for exchange in exchanges:
        offset = 0
        while True:
            r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
                params={"select": "ticker,exchange,company,yahoo_ticker",
                        "exchange": f"eq.{exchange}", "in_universe": "eq.true",
                        "limit": "1000", "offset": str(offset)})
            batch = r.json()
            if not isinstance(batch, list) or not batch: break
            for s in batch:
                s['_region'] = region
                in_universe[(s['ticker'], s['exchange'])] = s
            offset += 1000
            if len(batch) < 1000: break
    for exchange in exchanges:
        offset = 0
        while True:
            r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
                params={"select": "ticker,exchange,mkt_cap,value_score,growth_score,combined_rank",
                        "exchange": f"eq.{exchange}",
                        "limit": "1000", "offset": str(offset)})
            batch = r.json()
            if not isinstance(batch, list) or not batch: break
            for f in batch:
                key = (f['ticker'], f['exchange'])
                if key in in_universe:
                    funds_map[key] = f
            offset += 1000
            if len(batch) < 1000: break

print(f"Pool totale regioni attive: {len(funds_map)} titoli")

sorted_tickers = sorted(
    [(k, v) for k, v in funds_map.items()],
    key=lambda x: x[1].get('mkt_cap') or 0,
    reverse=True
)

# Rotazione: se il set di regioni attive e' cambiato dall'ultima
# esecuzione (es. l'Asia ha appena chiuso, l'Europa e' subentrata),
# riparte da zero sul nuovo pool. Altrimenti avanza di CHUNK_SIZE.
state = load_state()
if sorted(state.get("active_regions", [])) != sorted(active):
    print("Regioni attive cambiate rispetto all'ultima esecuzione — indice resettato")
    index = 0
else:
    index = state.get("index", 0)

total = len(sorted_tickers)
if total == 0:
    chunk = []
else:
    index = index % total
    end = index + CHUNK_SIZE
    chunk = sorted_tickers[index:end]
    if end > total:
        chunk += sorted_tickers[0:end - total]  # wrap-around

print(f"Chunk processato: {len(chunk)} titoli (indice {index} su {total})")

from concurrent.futures import ThreadPoolExecutor, as_completed

def process_ticker(args):
    (ticker, exchange), fund = args
    stock = in_universe.get((ticker, exchange), {})
    company      = stock.get('company', '') or ''
    region       = stock.get('_region', 'americas')
    yahoo_ticker = stock.get('yahoo_ticker') or (ticker + YAHOO_SUFFIX.get(exchange, ''))
    news = fetch_ticker_news(ticker, exchange, company, yahoo_ticker)
    rows = [{
        "ticker": ticker, "exchange": exchange, "region": region,
        "company": company, "yahoo_ticker": yahoo_ticker,
        "title": n['title'], "link": n['link'],
        "pub_date": n['pubDate'], "source": n['source'],
        "value_score": fund.get('value_score'),
        "growth_score": fund.get('growth_score'),
        "best_score": fund.get('combined_rank'),
        "mkt_cap": fund.get('mkt_cap'),
        "fetched_at": NOW,
    } for n in news]
    return rows

ok = fail = news_count = 0
all_rows = []

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(process_ticker, item): item for item in chunk}
    for future in as_completed(futures):
        try:
            rows = future.result()
            if rows:
                all_rows.extend(rows)
                ok += 1
            else:
                fail += 1
        except:
            fail += 1

write_ok = write_fail = 0
for i in range(0, len(all_rows), 200):
    batch = all_rows[i:i+200]
    success = False
    for attempt in range(3):
        try:
            resp = requests.post(SUPABASE_URL + "/rest/v1/news_cache", headers=headers_up, json=batch, timeout=30)
            if resp.status_code in (200, 201, 204):
                success = True
                break
            print(f"  WARN batch news rifiutato: HTTP {resp.status_code} — {resp.text[:200]}")
        except Exception as e:
            print(f"  WARN errore rete batch news: {e}")
        import time as _time
        _time.sleep(2 * (attempt + 1))
    if success:
        write_ok += len(batch)
        news_count += len(batch)
    else:
        write_fail += len(batch)
        print(f"  FALLITO DEFINITIVO: batch di {len(batch)} righe non scritto dopo 3 tentativi")

print(f"ok={ok} fail={fail} notizie_scritte={write_ok} notizie_fallite={write_fail}")

# Salva stato per la prossima rotazione
save_state({"active_regions": active, "index": index + CHUNK_SIZE})
print(f"Stato salvato: prossimo indice {(index + CHUNK_SIZE) % max(total,1)}")


print("Fetch news cache completato")
