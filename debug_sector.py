import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

# Conta TUTTI i titoli IT in stocks per US+TSX, con paginazione, senza altri filtri
all_stocks = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,in_universe","exchange":"in.(US,TSX)","sector":"eq.Information Technology",
                 "limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_stocks.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"Totale titoli IT in stocks (US+TSX), TUTTI: {len(all_stocks)}")
in_universe_count = sum(1 for s in all_stocks if s.get("in_universe"))
print(f"  di cui in_universe=true: {in_universe_count}")

# Ora conta quanti di questi hanno value_score non nullo in fundamentals
tickers_ex = [(s["ticker"], s["exchange"]) for s in all_stocks]
count_with_score = 0
count_checked = 0
for t, ex in tickers_ex[:400]:  # campione per velocita'
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"value_score","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
    d = r2.json()
    count_checked += 1
    if d and d[0].get("value_score") is not None:
        count_with_score += 1

print(f"\nCampione controllato: {count_checked}")
print(f"  di cui con value_score non nullo: {count_with_score}")
