import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EXCHANGES = {
    "US": "US", "TSX": "Canada",
    "XETRA": "Germania", "LSE": "UK", "AS": "Olanda", "PA": "Francia",
    "MIL": "Italia", "SWX": "Svizzera", "MC": "Spagna",
    "TSE": "Giappone", "SEHK": "HongKong", "ASX": "Australia", "KRX": "Corea", "SGX": "Singapore",
}

for exch, label in EXCHANGES.items():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"20"})
    tickers = [s["ticker"] for s in r.json()] if isinstance(r.json(),list) else []
    dates = {}
    for t in tickers:
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{exch}","order":"date.desc","limit":"1"})
        d = rp.json()
        date_val = d[0]["date"] if isinstance(d,list) and d else "VUOTO"
        dates[date_val] = dates.get(date_val, 0) + 1
    print(f"{exch} ({label}): {dates}")
