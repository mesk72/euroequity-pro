#!/usr/bin/env python3
# ============================================================
# FORWARDALPHA — DOWNLOAD STORICO 5 ANNI DA YAHOO FINANCE
# Scarica 5 anni di prezzi adjusted per tutti i titoli in universe
# Da eseguire UNA VOLTA per popolare prices_eod
# Poi i daily_*_yahoo.py mantengono i dati aggiornati
# ============================================================
# SCHEDULE CONSIGLIATO:
#   APAC:   12:00 CET (dopo chiusura Asia)
#   EU:     20:00 CET (dopo chiusura Europa)
#   US/CA:  02:00 CET (dopo chiusura USA)
# ============================================================

import os, time, random, requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

SUPABASE_URL  = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY   = os.environ.get("SUPABASE_SERVICE_KEY", "")
TODAY         = datetime.now().strftime("%Y-%m-%d")
START_5Y      = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
CHUNK         = 150  # titoli per batch

headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
              "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

# ── SUFFISSI YAHOO PER EXCHANGE ──────────────────────────────
YAHOO_SUFFIX = {
    "MIL": ".MI",  "XETRA": ".DE", "PA": ".PA",  "AS": ".AS",
    "MC":  ".MC",  "BR":    ".BR", "LS": ".LS",  "VI": ".VI",
    "HE":  ".HE",  "IR":    ".IR", "AT": ".VI",
    "LSE": ".L",   "AIM":   ".L",  "SWX": ".SW",
    "OM":  ".ST",  "NGM":   ".ST", "OB":  ".OL", "CPSE": ".CO",
    "US":  "",     "TSX":   ".TO",
    "TSE": ".T",   "SEHK":  ".HK", "ASX": ".AX",
    "KRX": ".KS",  "SGX":   ".SI",
}

SPECIAL_YAHOO = {
    "ROG": "ROG.SW", "BP.": "BP.L", "RR.": "RR.L",
    "BT.A": "BT-A.L", "BA.": "BA.L", "NG.": "NG.L",
}

def yahoo_ticker(ticker, exchange):
    if ticker in SPECIAL_YAHOO: return SPECIAL_YAHOO[ticker]
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    if exchange == "TSE":
        return (ticker.lstrip("0") or "0") + ".T" if ticker.isdigit() else ticker + ".T"
    if exchange == "KRX": return ticker.lstrip("A") + ".KS"
    if exchange == "SGX": return ticker + ".SI"
    if exchange in ("OM", "NGM", "CPSE"):
        return ticker.replace(" ", "-") + YAHOO_SUFFIX.get(exchange, "")
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":  return ticker.replace(".", "") + YAHOO_SUFFIX.get(exchange, "")
    return ticker.rstrip(".") + YAHOO_SUFFIX.get(exchange, "")

# ── INDICI (da aggiornare in tabella indices) ─────────────────
INDICES = [
    # EU
    ("^GDAXI",  "XETRA", "GDAXI",  "DAX"),
    ("^FCHI",   "PA",    "FCHI",   "CAC 40"),
    ("^AEX",    "AS",    "AEX",    "AEX"),
    ("^IBEX",   "MC",    "IBEX",   "IBEX 35"),
    ("^BFX",    "BR",    "BFX",    "BEL 20"),
    ("^SSMI",   "SWX",   "SMI",    "SMI"),
    ("^ATX",    "VI",    "ATX",    "ATX"),
    ("^OMX",    "OM",    "OMXS30", "OMX Stockholm"),
    ("^OMXC25", "CPSE",  "C25",    "OMX Copenhagen"),
    ("^OMXH25", "HE",    "HEX",    "OMX Helsinki"),
    ("^STOXX50E","EZ",   "SX5E",   "Euro Stoxx 50"),
    ("^STOXX",  "EZ",    "SXXP",   "STOXX 600"),
    # NA
    ("^GSPC",   "US",    "GSPC",   "S&P 500"),
    ("^IXIC",   "US",    "IXIC",   "Nasdaq"),
    ("^DJI",    "US",    "DJI",    "Dow Jones"),
    ("^GSPTSE", "TSX",   "GSPTSE", "TSX"),
    # APAC
    ("^N225",   "TSE",   "N225",   "Nikkei 225"),
    ("^HSI",    "SEHK",  "HSI",    "Hang Seng"),
    ("^AXJO",   "ASX",   "AXJO",   "ASX 200"),
    ("^KS11",   "KRX",   "KS11",   "KOSPI"),
    ("^STI",    "SGX",   "STI",    "STI Singapore"),
]

def update_indices():
    print("\n[INDICI] Aggiornamento indici...")
    for yt, exchange, code, name in INDICES:
        try:
            data = yf.download(yt, start=START_5Y, end=TODAY, interval="1d",
                               auto_adjust=False, progress=False)
            if data.empty: print(f"  {name}: vuoto"); continue
            rows = []
            for d, row in data.iterrows():
                close = row.get("Close") or row.get("Adj Close")
                if close and float(close) > 0:
                    rows.append({"ticker": code, "exchange": exchange,
                                 "date": d.strftime("%Y-%m-%d"), "close": round(float(close), 4)})
            if rows:
                r = requests.post(SUPABASE_URL + "/rest/v1/indices",
                    headers=headers_up, json=rows)
                print(f"  {name}: {len(rows)} righe salvate")
        except Exception as e:
            print(f"  {name}: errore {e}")
        time.sleep(1)

def load_universe(exchanges):
    """Carica tutti i titoli in universe per gli exchange specificati"""
    all_stocks = []
    for exchange in exchanges:
        offset = 0
        while True:
            r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
                params={"select": "ticker,exchange,yahoo_ticker",
                        "in_universe": "eq.true",
                        "exchange": "eq." + exchange,
                        "limit": "1000", "offset": str(offset)})
            batch = r.json()
            if not isinstance(batch, list) or not batch: break
            all_stocks.extend(batch)
            offset += 1000
            if len(batch) < 1000: break
    return all_stocks

def get_last_dates(stocks):
    """Legge ultima data disponibile per ogni titolo da prices_eod"""
    last = {}
    for s in stocks:
        r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select": "date", "ticker": "eq." + s["ticker"],
                    "exchange": "eq." + s["exchange"],
                    "order": "date.desc", "limit": "1"})
        row = r.json()
        last[(s["ticker"], s["exchange"])] = row[0]["date"] if isinstance(row, list) and row else "2020-01-01"
    return last

def download_prices(stocks, last_dates, market_name):
    """Scarica prezzi per un gruppo di titoli"""
    from collections import defaultdict
    by_exchange = defaultdict(list)
    for s in stocks:
        by_exchange[s["exchange"]].append(s)

    price_buf = []
    ok = fail = skip = 0

    for exchange, exchange_stocks in by_exchange.items():
        tickers = [s["ticker"] for s in exchange_stocks]
        stock_map = {s["ticker"]: s for s in exchange_stocks}

        for i in range(0, len(tickers), CHUNK):
            chunk_tickers = tickers[i:i+CHUNK]
            ytickers = []
            ticker_map = {}

            for tk in chunk_tickers:
                last = last_dates.get((tk, exchange), "2020-01-01")
                if last >= TODAY:
                    skip += 1; continue
                s = stock_map[tk]
                yt = s.get("yahoo_ticker") or yahoo_ticker(tk, exchange)
                ytickers.append(yt)
                ticker_map[yt] = (tk, exchange)

            if not ytickers: continue

            # Data di partenza
            starts = [last_dates.get((ticker_map[yt][0], ticker_map[yt][1]), "2020-01-01") for yt in ytickers]
            start_dt = min(starts)
            start_dt = (datetime.strptime(start_dt, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

            # Non scaricare se già aggiornato
            if start_dt > TODAY:
                skip += len(ytickers); continue

            try:
                data_yf = yf.download(
                    tickers=" ".join(ytickers),
                    start=start_dt, end=TODAY,
                    interval="1d", auto_adjust=True,
                    progress=False, threads=True,
                )
                if data_yf.empty:
                    fail += len(ytickers); continue

                # Gestisci sia single che multi ticker
                if len(ytickers) == 1:
                    closes = pd.DataFrame(data_yf["Close"])
                    closes.columns = ytickers
                else:
                    closes = data_yf["Close"] if "Close" in data_yf.columns else data_yf

                for yt in ytickers:
                    if yt not in closes.columns:
                        fail += 1; continue
                    tk, ex = ticker_map[yt]
                    last = last_dates.get((tk, ex), "2020-01-01")
                    count = 0
                    for date_idx, price in closes[yt].dropna().items():
                        date_str = date_idx.strftime("%Y-%m-%d")
                        if date_str <= last: continue
                        price_buf.append({
                            "ticker": tk, "exchange": ex,
                            "date": date_str, "adj_close": round(float(price), 6)
                        })
                        count += 1
                    if count > 0: ok += 1
                    else: fail += 1

            except Exception as e:
                print(f"    Errore {exchange} chunk {i//CHUNK+1}: {e}")
                fail += len(ytickers)

            # Salva ogni 500 righe
            if len(price_buf) >= 500:
                resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod",
                    headers=headers_up, json=price_buf)
                print(f"  Salvate {len(price_buf)} righe ({market_name} {exchange} chunk {i//CHUNK+1})")
                price_buf = []

            # Pausa random
            pause = random.uniform(3.0, 7.0)
            print(f"  {exchange} chunk {i//CHUNK+1}/{len(tickers)//CHUNK+1} — pausa {pause:.1f}s")
            time.sleep(pause)

    # Salva residui
    if price_buf:
        requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf)
        print(f"  Salvate {len(price_buf)} righe finali ({market_name})")

    print(f"  {market_name}: ok={ok} fail={fail} skip={skip}")
    return ok, fail

# ── MAIN ────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    market = sys.argv[1] if len(sys.argv) > 1 else "all"

    print(f"ForwardAlpha — Download Storico 5 anni ({market.upper()})")
    print(f"Da: {START_5Y} A: {TODAY}")

    if market in ("eu", "all"):
        print("\n=== EUROPA ===")
        EU_EXCHANGES = ["MIL","XETRA","PA","LSE","OM","SWX","OB","AS","MC","BR","CPSE","HE","VI","IR","LS","AIM","NGM","AT"]
        stocks = load_universe(EU_EXCHANGES)
        print(f"  {len(stocks)} titoli EU")
        last = get_last_dates(stocks)
        download_prices(stocks, last, "EU")

    if market in ("us", "all"):
        print("\n=== NORD AMERICA ===")
        stocks = load_universe(["US", "TSX"])
        print(f"  {len(stocks)} titoli US+CA")
        last = get_last_dates(stocks)
        download_prices(stocks, last, "NA")

    if market in ("apac", "all"):
        print("\n=== ASIA PACIFIC ===")
        stocks = load_universe(["TSE", "SEHK", "ASX", "KRX", "SGX"])
        print(f"  {len(stocks)} titoli APAC")
        last = get_last_dates(stocks)
        download_prices(stocks, last, "APAC")

    if market in ("indices", "all"):
        update_indices()

    print("\nFINE.")
