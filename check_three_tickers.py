import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Stessa identica query usata nello script, isolata
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker,exchange,date,adj_close","exchange":"eq.US",
             "order":"ticker.asc,date.desc","limit":"1000","offset":"0"})
print("Status:", r.status_code)
print("Numero righe:", len(r.json()) if isinstance(r.json(), list) else "N/A")
print("Corpo risposta (primi 500 char):", r.text[:500])
