import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

sectors = ["Information Technology", "Financials", "Healthcare"]

# Scarica UNA VOLTA tutti i fundamentals US con implied_growth valido (poche chiamate)
fund_with_data = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","mkt_cap":"not.is.null","implied_growth_10y":"not.is.null",
                 "limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    fund_with_data.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

tickers_with_data = set(f["ticker"] for f in fund_with_data)
print(f"Totale ticker US con implied_growth valido: {len(tickers_with_data)}\n")

for sec in sectors:
    r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","exchange":"eq.US","sector":f"eq.{sec}","in_universe":"eq.true"})
    total = int(r1.headers.get("content-range","").split("/")[-1])

    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.US","sector":f"eq.{sec}","in_universe":"eq.true","limit":"1000"})
    sector_tickers = set(s["ticker"] for s in r2.json())

    count_with_data = len(sector_tickers & tickers_with_data)
    print(f"{sec}: {count_with_data} su {total} hanno implied growth calcolabile ({round(count_with_data/total*100,1)}% copertura)")
