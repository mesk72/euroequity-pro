import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY = os.environ.get("LEEWAY_KEY", "")
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

r = requests.get(f"https://api.leeway.tech/api/v1/public/historicalquotes/SGU.US?apitoken={LEEWAY_KEY}&from=2026-07-08&to=2026-07-11", timeout=15)
print(f"Fetch SGU: HTTP {r.status_code}")
data = r.json()
buf = [{"ticker":"SGU","exchange":"US","date":row["date"],"adj_close":float(row.get("adjusted_close") or row.get("close"))} for row in data]
resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod?on_conflict=ticker,exchange,date", headers=headers_up, json=buf, timeout=30)
print(f"Scrittura: HTTP {resp.status_code}")

rv = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers={"apikey":SERVICE_KEY,"Authorization":"Bearer "+SERVICE_KEY},
    params={"select":"date","ticker":"eq.SGU","exchange":"eq.US","order":"date.desc","limit":"1"})
print(f"Verifica SGU: {rv.json()}")
