import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"ticker,date,adj_close","exchange":"eq.TSE","order":"date.desc","limit":"5"})
print("Ultime 5 righe TSE (qualsiasi ticker):")
for row in r.json():
    print(" ", row)
