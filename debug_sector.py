import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Replica ESATTA della logica dell'endpoint, per NVDA (US, Information Technology)
exchange_list = ["US","TSX"]
sector = "Information Technology"

# stocks (per sector)
stocks_data = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,sector","exchange":"in.(US,TSX)","sector":f"eq.{sector}","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    stocks_data.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

# fundamentals (mkt_cap, scores) - TUTTI i settori per US+TSX, poi filtro dopo
fund_data = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,value_score,growth_score,combined_rank,mkt_cap","exchange":"in.(US,TSX)","value_score":"not.is.null","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    fund_data.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"Stocks IT trovati: {len(stocks_data)}")
print(f"Fundamentals totali US+TSX: {len(fund_data)}")

sector_map = {f"{s['ticker']}.{s['exchange']}": s['sector'] for s in stocks_data}

data = []
for f in fund_data:
    key = f"{f['ticker']}.{f['exchange']}"
    sec = sector_map.get(key)
    mktcap = f.get("mkt_cap") or 0
    if sec and mktcap > 0:
        data.append({**f, "sector": sec, "mktCap": mktcap})

print(f"Righe finali unite (IT, con mktCap valido): {len(data)}")

if data:
    cap_sum = sum(d["mktCap"] for d in data)
    val_wsum = sum((d.get("value_score") or 0) * d["mktCap"] for d in data)
    grw_wsum = sum((d.get("growth_score") or 0) * d["mktCap"] for d in data)
    rank_wsum = sum((d.get("combined_rank") or 0) * d["mktCap"] for d in data)
    print(f"\nInformation Technology, North America:")
    print(f"  Titoli: {len(data)}")
    print(f"  Value Score medio (weighted): {round(val_wsum/cap_sum,1)}")
    print(f"  Growth Score medio (weighted): {round(grw_wsum/cap_sum,1)}")
    print(f"  Best Score medio (weighted): {round(rank_wsum/cap_sum,1)}")
else:
    print("NESSUN DATO — c'e' ancora un problema")
