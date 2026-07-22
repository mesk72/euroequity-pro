#!/usr/bin/env python3
# FORWARDALPHA — RIPOPOLAMENTO STORICO COMPLETO 5 ANNI, SOLO YAHOO
# Da eseguire UNA VOLTA dopo aver svuotato prices_eod. Copre tutti i
# 23 mercati, chunk da 150 titoli per chiamata Yahoo (schema gia'
# collaudato dai daily script), data fissa a 5 anni fa per tutti
# (la tabella e' vuota, non serve controllare "ultima data" per titolo).

import os, time, random, requests
import yfinance as yf
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json"}

TODAY = datetime.now().strftime("%Y-%m-%d")
START = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR',
              'LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX',
              'KRX','SGX','US']

YAHOO_SUFFIX = {"US": ""}

def yahoo_ticker(ticker, exchange, override=None):
    if override:
        return override
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "TSE":
        return ticker.lstrip("0") + ".T" if ticker.isdigit() else ticker + ".T"
    if exchange == "KRX": return ticker.lstrip("A") + ".KS"
    if exchange == "SGX": return ticker + ".SI"
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    MAP = {'PA':'.PA','XETRA':'.DE','MIL':'.MI','MC':'.MC','AS':'.AS',
           'BR':'.BR','LSE':'.L','SWX':'.SW','OM':'.ST','OB':'.OL',
           'HE':'.HE','IR':'.IR','VI':'.VI','CPSE':'.CO','NGM':'.ST',
           'ASX':'.AX'}
    return ticker + MAP.get(exchange, YAHOO_SUFFIX.get(exchange, ""))

print(f"Periodo: {START} -> {TODAY}")
print("=" * 60)

total_ok = total_fail = total_rows = 0

for exchange in ALL_RANKED:
    print(f"\n{exchange}...")
    all_stocks = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker,exchange,yahoo_ticker", "exchange": f"eq.{exchange}",
                     "in_universe": "eq.true", "limit": "1000", "offset": str(offset)})
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        all_stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

    print(f"  Titoli in universo: {len(all_stocks)}")
    if not all_stocks:
        continue

    CHUNK = 150
    price_buf = []
    ok = fail = 0

    for i in range(0, len(all_stocks), CHUNK):
        chunk = all_stocks[i:i+CHUNK]
        ytickers = []
        ticker_map = {}
        for s in chunk:
            yt = s.get("yahoo_ticker") or yahoo_ticker(s["ticker"], exchange)
            ytickers.append(yt)
            ticker_map[yt] = (s["ticker"], exchange)

        try:
            data_yf = yf.download(
                tickers=" ".join(ytickers), start=START, end=TODAY,
                interval="1d", auto_adjust=True, progress=False, threads=True,
            )
            if data_yf.empty:
                fail += len(ytickers)
                continue
            closes = data_yf[["Close"]].rename(columns={"Close": ytickers[0]}) if len(ytickers) == 1 else data_yf["Close"]
            for yt in ytickers:
                if yt not in closes.columns:
                    fail += 1
                    continue
                tk, ex = ticker_map[yt]
                n_rows = 0
                for date_idx, price in closes[yt].dropna().items():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    price_buf.append({"ticker": tk, "exchange": ex, "date": date_str, "adj_close": round(float(price), 6)})
                    n_rows += 1
                if n_rows > 0:
                    ok += 1
                else:
                    fail += 1
        except Exception as e:
            print(f"    Errore chunk {i}: {e}")
            fail += len(ytickers)

        if len(price_buf) >= 3000:
            for j in range(0, len(price_buf), 1000):
                requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_up, json=price_buf[j:j+1000])
            total_rows += len(price_buf)
            price_buf = []

        time.sleep(random.uniform(3.0, 7.0))

    if price_buf:
        for j in range(0, len(price_buf), 1000):
            requests.post(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_up, json=price_buf[j:j+1000])
        total_rows += len(price_buf)

    print(f"  {exchange}: ok={ok} fail={fail}")
    total_ok += ok
    total_fail += fail

print("\n" + "=" * 60)
print(f"TOTALE: ok={total_ok} fail={total_fail} righe_scritte={total_rows}")
