import os, requests, random
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# campione casuale di 50 ticker US dall'universo
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","exchange":"eq.US","in_universe":"eq.true","limit":"3000"}, timeout=30)
universe = [row["ticker"] for row in r.json()]
sample = random.sample(universe, 50)

dates = {}
for t in sample:
    rr = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{t}","exchange":"eq.US","order":"date.desc","limit":"1"}, timeout=15)
    d = rr.json()
    date_val = d[0]["date"] if d else "VUOTO"
    dates[date_val] = dates.get(date_val, 0) + 1

print(f"Campione di {len(sample)} titoli US casuali:")
for d, c in sorted(dates.items(), reverse=True):
    print(f"  {d}: {c}")
