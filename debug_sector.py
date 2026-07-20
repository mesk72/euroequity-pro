import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

# 1. Tutti con sector=Financials, US+TSX
r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","exchange":"in.(US,TSX)","sector":"eq.Financials"})
print("TOTALE stocks sector=Financials US+TSX:", r1.headers.get("content-range"))

# 2. Solo in_universe=true
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","exchange":"in.(US,TSX)","sector":"eq.Financials","in_universe":"eq.true"})
print("Con in_universe=true:", r2.headers.get("content-range"))

# 3. Solo US (non TSX) - forse "Nord America" nello screener e' solo US
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","exchange":"eq.US","sector":"eq.Financials","in_universe":"eq.true"})
print("Solo US, in_universe=true:", r3.headers.get("content-range"))

# 4. Quanti hanno anche value_score non nullo in fundamentals (join manuale)
r4 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange","exchange":"in.(US,TSX)","sector":"eq.Financials","in_universe":"eq.true","limit":"1000"})
tickers = [(s["ticker"], s["exchange"]) for s in r4.json()]
count_with_score = 0
for t, ex in tickers[:300]:
    rf = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"value_score","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
    d = rf.json()
    if d and d[0].get("value_score") is not None:
        count_with_score += 1
print(f"Campione 300 con in_universe=true, di cui con value_score valido: {count_with_score}")
