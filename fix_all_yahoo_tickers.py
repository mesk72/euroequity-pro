import os, requests, re

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

# Suffissi Yahoo Finance per borsa (confermati da sessioni precedenti + standard Yahoo)
SUFFIX = {
    "US": "", "TSX": ".TO", "MIL": ".MI", "XETRA": ".DE", "PA": ".PA",
    "LSE": ".L", "SWX": ".SW", "OM": ".ST", "AS": ".AS", "MC": ".MC",
    "BR": ".BR", "HE": ".HE", "CPSE": ".CO", "OB": ".OL", "GR": ".AT",
    "VI": ".VI", "IR": ".IR", "LS": ".LS",
    "TSE": ".T", "SEHK": ".HK", "ASX": ".AX", "KRX": ".KS", "SGX": ".SI",
}

def build_yahoo_ticker(ticker, exchange):
    suffix = SUFFIX.get(exchange, "")
    base = ticker
    if exchange == "US":
        # Yahoo usa il trattino per le classi azionarie (BRK.A -> BRK-A)
        base = base.replace(".", "-")
    return base + suffix

exchanges = list(SUFFIX.keys())
total_fixed = 0
for ex in exchanges:
    offset = 0
    to_update = []
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true",
                     "yahoo_ticker":"is.null","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch:
            yt = build_yahoo_ticker(s["ticker"], ex)
            to_update.append({"ticker": s["ticker"], "exchange": ex, "yahoo_ticker": yt})
        offset += 1000
        if len(batch) < 1000: break

    if to_update:
        ok = 0
        for i in range(0, len(to_update), 200):
            chunk = to_update[i:i+200]
            resp = requests.post(SUPABASE_URL + "/rest/v1/stocks?on_conflict=ticker,exchange",
                headers=headers_up, json=chunk, timeout=30)
            if resp.status_code in (200,201,204):
                ok += len(chunk)
            else:
                print(f"  WARN {ex}: HTTP {resp.status_code} {resp.text[:150]}")
        print(f"{ex}: {ok}/{len(to_update)} yahoo_ticker aggiornati")
        total_fixed += ok

print(f"\nTOTALE aggiornati: {total_fixed}")
