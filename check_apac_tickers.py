import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,company","exchange":"eq.SEHK","company":"ilike.*Tencent*"})
print("SEHK Tencent:", r.json())
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,company","exchange":"eq.KRX","company":"ilike.*Samsung Electr*"})
print("KRX Samsung:", r2.json())

# campione ampio: quanti SGX e KRX sono fermi al 3 luglio vs aggiornati
for exch in ["SGX","KRX","SEHK","TSE","ASX"]:
    r3 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"15"})
    tickers = [s["ticker"] for s in r3.json()] if isinstance(r3.json(),list) else []
    dates = []
    for t in tickers[:8]:
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{exch}","order":"date.desc","limit":"1"})
        d = rp.json()
        dates.append(d[0]["date"] if isinstance(d,list) and d else "VUOTO")
    print(f"{exch} campione date (8 titoli): {dates}")
