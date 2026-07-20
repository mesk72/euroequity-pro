import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def fetch_all(table, params_extra, limit=1000):
    all_rows = []
    offset = 0
    while True:
        p = {**params_extra, "limit": str(limit), "offset": str(offset)}
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers_r, params=p)
        batch = r.json()
        if not isinstance(batch, list) or not batch: break
        all_rows.extend(batch)
        offset += limit
        if len(batch) < limit: break
    return all_rows

sector = "Information Technology"

# A) stocks con sector=IT, US+TSX, TUTTI (nessun filtro universo)
a = fetch_all("stocks", {"select":"ticker,exchange,in_universe","exchange":"in.(US,TSX)","sector":f"eq.{sector}"})
print(f"A) stocks IT US+TSX, TUTTI: {len(a)}")

# B) + in_universe=true
b = [x for x in a if x.get("in_universe")]
print(f"B) + in_universe=true: {len(b)}")

# C) + esistenza in fundamentals (qualsiasi riga, anche senza value_score)
fund_all = fetch_all("fundamentals", {"select":"ticker,exchange","exchange":"in.(US,TSX)"})
fund_keys = set((f["ticker"], f["exchange"]) for f in fund_all)
c = [x for x in b if (x["ticker"], x["exchange"]) in fund_keys]
print(f"C) B + esiste riga in fundamentals: {len(c)}")

# D) + value_score non nullo specificamente
fund_with_score = fetch_all("fundamentals", {"select":"ticker,exchange","exchange":"in.(US,TSX)","value_score":"not.is.null"})
score_keys = set((f["ticker"], f["exchange"]) for f in fund_with_score)
d = [x for x in b if (x["ticker"], x["exchange"]) in score_keys]
print(f"D) B + value_score non nullo: {len(d)}")

# E) + mkt_cap valido (>0) in fundamentals, quello richiesto dal mio endpoint sector-averages
fund_with_cap = fetch_all("fundamentals", {"select":"ticker,exchange,mkt_cap","exchange":"in.(US,TSX)","value_score":"not.is.null"})
cap_keys = set((f["ticker"], f["exchange"]) for f in fund_with_cap if f.get("mkt_cap") and f["mkt_cap"] > 0)
e = [x for x in b if (x["ticker"], x["exchange"]) in cap_keys]
print(f"E) B + value_score non nullo + mkt_cap>0: {len(e)}")
