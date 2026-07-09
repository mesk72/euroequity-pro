import os, requests, time
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
try:
    import yfinance as yf
except ImportError:
    raise SystemExit("Manca yfinance")

all_stocks = []
for exch in ["SGX","KRX"]:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange,yahoo_ticker","exchange":f"eq.{exch}",
                    "in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        all_stocks.extend(batch)
        offset += 1000
        if len(batch) < 1000: break
print(f"Titoli SGX+KRX in_universe: {len(all_stocks)}")

def yahoo_ticker(ticker, exchange):
    if exchange == "KRX": return ticker.lstrip("A") + ".KS"  # tentativo iniziale, fallback sotto
    if exchange == "SGX": return ticker + ".SI"
    return ticker

ok_w = ok_beta = fail = 0
website_batch = []
beta_batch = []
for i, s in enumerate(all_stocks):
    ticker, exchange = s["ticker"], s["exchange"]
    yt = s.get("yahoo_ticker") or yahoo_ticker(ticker, exchange)
    try:
        info = yf.Ticker(yt).info
        website = info.get("website")
        beta = info.get("beta")
        if not website and exchange == "KRX":
            # fallback KOSDAQ
            yt2 = ticker.lstrip("A") + ".KQ"
            info2 = yf.Ticker(yt2).info
            website = website or info2.get("website")
            beta = beta or info2.get("beta")
            yt = yt2 if info2.get("website") else yt
        if website:
            website_batch.append({"ticker": ticker, "exchange": exchange, "website": website})
            ok_w += 1
        if beta:
            beta_batch.append({"ticker": ticker, "exchange": exchange, "beta": round(float(beta),3)})
            ok_beta += 1
        if not s.get("yahoo_ticker") and (website or beta):
            requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
                params={"ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"}, json={"yahoo_ticker": yt})
    except Exception:
        fail += 1
    if len(website_batch) >= 100:
        requests.post(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up, json=website_batch)
        website_batch = []
    if len(beta_batch) >= 100:
        requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_up, json=beta_batch)
        beta_batch = []
    if (i+1) % 100 == 0:
        print(f"  ...{i+1}/{len(all_stocks)} — website={ok_w} beta={ok_beta} fail={fail}")
    time.sleep(0.2)

if website_batch: requests.post(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up, json=website_batch)
if beta_batch: requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_up, json=beta_batch)
print(f"\nFinale: website={ok_w}/{len(all_stocks)} beta={ok_beta}/{len(all_stocks)} fail={fail}")
