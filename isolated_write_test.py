import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type":"application/json"}

# Replica ESATTA di quello che fa daily_us.py per un titolo solo
url = f"https://api.leeway.tech/api/v1/public/historicalquotes/JPM.US?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11"
r = requests.get(url, timeout=20)
print(f"Fetch: HTTP {r.status_code}")
data = r.json()
price_buf = []
for row in data:
    adj = row.get("adjusted_close") or row.get("close")
    price_buf.append({"ticker": "JPM", "exchange": "US", "date": row["date"], "adj_close": float(adj)})
print(f"Righe da scrivere: {len(price_buf)}")
print(price_buf)

resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf, timeout=30)
print(f"Scrittura: HTTP {resp.status_code}")
print(resp.text[:500])

# Verifica immediata
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY},
    params={"select":"date","ticker":"eq.JPM","exchange":"eq.US","order":"date.desc","limit":"1"})
print(f"Verifica dopo scrittura: {r2.json()}")
