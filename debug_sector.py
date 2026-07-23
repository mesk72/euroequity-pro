import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"20"})
sample = [s["ticker"] for s in r.json()]

print("Campione date piu' recenti per 20 titoli US casuali:")
dates_found = {}
for tk in sample:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":"eq.US","order":"date.desc","limit":"1"})
    d = r2.json()
    date_val = d[0]["date"] if d else "NESSUNO"
    dates_found[date_val] = dates_found.get(date_val, 0) + 1
    print(f"  {tk}: {date_val}")

print(f"\nRiepilogo: {dates_found}")
