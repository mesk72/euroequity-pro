#!/usr/bin/env python3
# FORWARDALPHA — FETCH NEWS CACHE
# Scarica notizie per top ticker per regione e salva in Supabase news_cache

import os, time, requests
from datetime import datetime, timedelta

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

# Limiti ticker: TOP aggiornati ogni ora, REST ogni 3 ore
TOP_LIMITS = {
    'americas': 200,  # top 200 ogni ora, restanti 1300 ogni 3 ore
    'europe':   50,   # top 50 ogni ora, restanti 1450 ogni 3 ore
    'asia':     50,   # top 50 ogni ora, restanti 1450 ogni 3 ore
}

FULL_LIMITS = {
    'americas': 1500,
    'europe':   1500,
    'asia':     1500,
}

REGIONS = {
    'americas': ['US','TSX'],
    'europe':   ['PA','XETRA','MIL','MC','AS','BR','LSE','SWX','OM','OB','HE','IR','VI','CPSE'],
    'asia':     ['TSE','SEHK','ASX'],
}

import sys
# Se lanciato con argomento 'all' processa tutti i ticker, altrimenti solo top
PROCESS_ALL = 'all' in sys.argv

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
    # Yahoo Finance RSS
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={yahoo_ticker}&region=US&lang=en-US"
        r = requests.get(url, headers={'User-Agent': UA}, timeout=8)
        if r.status_code == 200:
            results.extend(parse_rss(r.text))
    except: pass
    # Google News RSS
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

# Pulisci notizie vecchie
requests.delete(SUPABASE_URL + "/rest/v1/news_cache",
    headers={**headers_r, "Content-Type": "application/json"},
    params={"fetched_at": f"lt.{AGO24}"})
print("Notizie vecchie eliminate")

for region, exchanges in REGIONS.items():
    print(f"\n{region.upper()}...")

    # 1. Leggi ticker in_universe da stocks (NON da fundamentals)
    in_universe = {}  # key: (ticker,exchange) -> True
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
                in_universe[(s['ticker'], s['exchange'])] = s
            offset += 1000
            if len(batch) < 1000: break
    print(f"  In universe: {len(in_universe)} titoli")

    # 2. Leggi fundamentals per score e mktcap
    funds_map = {}
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

    # 3. Ordina per mktcap, prendi top 1500
    sorted_tickers = sorted(
        [(k, v) for k, v in funds_map.items()],
        key=lambda x: x[1].get('mkt_cap') or 0,
        reverse=True
    )[:len(sorted_tickers)]  # prende tutti, poi filtra sotto

    # TOP: primi N per mktcap (ogni ora)
    # REST: dal N+1 in poi (ogni 3 ore) — no duplicati
    top_n  = TOP_LIMITS.get(region, 200)
    full_n = FULL_LIMITS.get(region, 1500)
    if PROCESS_ALL:
        to_process = sorted_tickers[top_n:full_n]  # solo i restanti
        print(f"  Modalità REST: {len(to_process)} ticker (dal {top_n+1} al {full_n})")
    else:
        to_process = sorted_tickers[:top_n]  # solo top
        print(f"  Modalità TOP: {len(to_process)} ticker")
    sorted_tickers = to_process
    print(f"  Top ticker: {len(sorted_tickers)}")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def process_ticker(args):
        (ticker, exchange), fund = args
        stock = in_universe.get((ticker, exchange), {})
        company      = stock.get('company', '') or ''
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

    # 20 thread paralleli — riduce tempo da 45min a ~5min
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_ticker, item): item for item in sorted_tickers}
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

    # Salva in batch
    for i in range(0, len(all_rows), 200):
        batch = all_rows[i:i+200]
        requests.post(SUPABASE_URL + "/rest/v1/news_cache", headers=headers_up, json=batch)
        news_count += len(batch)

    print(f"  ok={ok} fail={fail} notizie={news_count}")

print("\nFetch news cache completato")
