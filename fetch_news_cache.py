#!/usr/bin/env python3
# ============================================================
# FORWARDALPHA — FETCH NEWS CACHE
# Da eseguire ogni ora via GitHub Actions
# Scarica notizie per top 1500 ticker per regione
# e le salva in Supabase tabella news_cache
# Così gli utenti leggono da Supabase, non da Yahoo/Google
# ============================================================

import os, time, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

TODAY = datetime.now().strftime("%Y-%m-%d")
NOW   = datetime.now().isoformat()
AGO24 = (datetime.now() - timedelta(hours=24)).isoformat()

STOP = set(['Inc','Ltd','Corp','Group','SA','AG','NV','PLC','SE','Co',
    'The','Holdings','International','Global','Company','Corporation','Limited',
    'de','et','und','of','and'])

YAHOO_SUFFIX = {
    'PA':'.PA', 'XETRA':'.DE', 'MIL':'.MI', 'MC':'.MC',
    'AS':'.AS', 'BR':'.BR', 'LSE':'.L', 'SWX':'.SW',
    'OM':'.ST', 'OB':'.OL', 'HE':'.HE', 'IR':'.IR',
    'VI':'.VI', 'CPSE':'.CO', 'TSE':'.T', 'SEHK':'.HK',
    'ASX':'.AX', 'TSX':'.TO',
}

REGIONS = {
    'americas': ['US', 'TSX'],
    'europe':   ['PA','XETRA','MIL','MC','AS','BR','LSE','SWX','OM','OB','HE','IR','VI','CPSE'],
    'asia':     ['TSE','SEHK','ASX'],
}

import xml.etree.ElementTree as ET

def parse_rss(xml_text):
    items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.findall('.//item'):
            title   = item.findtext('title','').strip()
            link    = item.findtext('link','').strip()
            pubdate = item.findtext('pubDate','').strip()
            source  = item.findtext('source','').strip() or 'Yahoo Finance'
            if title and len(title) > 10:
                items.append({'title':title,'link':link,'pubDate':pubdate,'source':source})
    except: pass
    return items[:10]

def fetch_news_for_ticker(ticker, exchange, company, yahoo_ticker):
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

    # Deduplicazione
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
    params={"pub_date": f"lt.{AGO24}"})
print("Notizie vecchie eliminate")

for region, exchanges in REGIONS.items():
    print(f"\n{region.upper()}...")

    # Leggi top 1500 ticker per mktcap
    all_funds = []
    for exchange in exchanges:
        offset = 0
        while len(all_funds) < 1500:
            r = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
                params={"select": "ticker,exchange,mkt_cap,value_score,growth_score,combined_rank",
                        "exchange": f"eq.{exchange}", "in_universe": "eq.true",
                        "order": "mkt_cap.desc.nullslast",
                        "offset": str(offset), "limit": "1000"})
            batch = r.json()
            if not isinstance(batch, list) or not batch: break
            all_funds.extend(batch)
            offset += 1000
            if len(batch) < 1000: break

    # Leggi info stocks
    tickers_list = [f['ticker'] for f in all_funds[:1500]]
    stocks_map = {}
    for i in range(0, len(tickers_list), 500):
        chunk = tickers_list[i:i+500]
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange,company,yahoo_ticker",
                    "exchange": f"in.({chr(44).join(exchanges)})",
                    "ticker": f"in.({chr(44).join(chunk)})",
                    "limit": "500"})
        for s in r.json() or []:
            stocks_map[f"{s['ticker']}.{s['exchange']}"] = s

    ok = fail = 0
    news_buf = []
    for fund in all_funds[:1500]:
        ticker   = fund['ticker']
        exchange = fund['exchange']
        key      = f"{ticker}.{exchange}"
        stock    = stocks_map.get(key)
        if not stock: continue

        suffix      = YAHOO_SUFFIX.get(exchange, '')
        yahoo_ticker = stock.get('yahoo_ticker') or (ticker + suffix)
        company      = stock.get('company','')

        news = fetch_news_for_ticker(ticker, exchange, company, yahoo_ticker)
        for n in news:
            news_buf.append({
                "ticker":      ticker,
                "exchange":    exchange,
                "region":      region,
                "company":     company,
                "yahoo_ticker": yahoo_ticker,
                "title":       n['title'],
                "link":        n['link'],
                "pub_date":    n['pubDate'],
                "source":      n['source'],
                "value_score": fund.get('value_score'),
                "growth_score":fund.get('growth_score'),
                "best_score":  fund.get('combined_rank'),
                "mkt_cap":     fund.get('mkt_cap'),
                "fetched_at":  NOW,
            })

        if len(news) > 0: ok += 1
        else: fail += 1

        if len(news_buf) >= 200:
            requests.post(SUPABASE_URL + "/rest/v1/news_cache",
                headers=headers_up, json=news_buf)
            news_buf = []

        time.sleep(0.1)

    if news_buf:
        requests.post(SUPABASE_URL + "/rest/v1/news_cache",
            headers=headers_up, json=news_buf)

    print(f"  ok={ok} fail={fail} notizie={ok*3}")

print("\nFetch news cache completato")
