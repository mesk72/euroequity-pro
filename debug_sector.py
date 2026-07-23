import os, requests, datetime
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).isoformat()
r = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"ticker,exchange,region,fetched_at","fetched_at":f"gte.{cutoff}","limit":"1000"})
rows = r.json()
tickers = set((row["ticker"], row["exchange"]) for row in rows)
regions = {}
for row in rows:
    regions[row.get("region","?")] = regions.get(row.get("region","?"), 0) + 1

print(f"Righe totali ultime 24h (campione max 1000): {len(rows)}")
print(f"Ticker distinti con notizie fresche: {len(tickers)}")
print(f"Per regione: {regions}")
print(f"Esempio ticker coperti: {list(tickers)[:10]}")
