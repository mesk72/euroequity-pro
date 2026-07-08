import os, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

TODAY = datetime.now().strftime("%Y-%m-%d")
LEEWAY_SUFFIX = {"AS":".AS","XETRA":".XETRA","PA":".PA","SWX":".SW","LSE":".L",
                  "OM":".ST","OB":".OL","CPSE":".CO","MC":".MC","GR":".AT",
                  "VI":".VI","IR":".IR","LS":".LS","MIL":".MI"}

def leeway_ticker(ticker, exchange):
    if exchange == "SEHK": return ticker.zfill(4) + ".HK"
    ticker_clean = ticker.rstrip(".")
    return ticker_clean + LEEWAY_SUFFIX.get(exchange, "")

samples = [("ASML","AS"),("SAP","XETRA"),("BNP","PA"),("NESN","SWX")]

for ticker, exchange in samples:
    print("=" * 60)
    print(f"{ticker}.{exchange}")
    print("=" * 60)

    # 1. Ultima data in prices_eod
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                "order":"date.desc","limit":"1"})
    d = r.json()
    last = d[0]["date"] if isinstance(d,list) and d else "2021-01-01"
    print(f"  Ultima data DB: {last}")

    start_dt = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    lt = leeway_ticker(ticker, exchange)
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={start_dt}&to={TODAY}"
    print(f"  Ticker Leeway: {lt}")
    print(f"  Range: {start_dt} -> {TODAY}")

    try:
        resp = requests.get(url, timeout=15)
        print(f"  HTTP status: {resp.status_code}")
        body = resp.text[:400]
        print(f"  Body (primi 400 char): {body}")
    except Exception as e:
        print(f"  ECCEZIONE: {type(e).__name__}: {e}")

    # 2. Verifica anche se il titolo e' effettivamente in_universe
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,in_universe","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
    print(f"  Riga in 'stocks': {r2.json()}")
    print()

print("FATTO.")
