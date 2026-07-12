import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.4974","exchange":"eq.TSE","order":"date.desc","limit":"5"})
print("Takara Bio ultimi prezzi:", r.json())
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"price,mom12m,mkt_cap","ticker":"eq.4974","exchange":"eq.TSE"})
print("Fundamentals:", r2.json())

# Simula la formula del sito
current_cap = 846.5
ret = -0.999
implied_start = current_cap / (1 + ret)
print(f"\nCap di partenza implicita con la formula attuale: {implied_start:.1f}B (assurda)")
