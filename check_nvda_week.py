import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.NVDA","exchange":"eq.US","date":"gte.2026-06-28","date2":"lte.2026-07-10","order":"date.asc","limit":"15"})
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.NVDA","exchange":"eq.US","date":"gte.2026-06-28","order":"date.asc","limit":"15"})
print("NVDA prezzi 28 giu - 10 lug:")
for row in r2.json():
    print(f"  {row}")

# Verifica quale giorno da' esattamente +8.28%
latest = 210.96
for row in r2.json():
    pct = (latest/row['adj_close']-1)*100
    print(f"  vs {row['date']} ({row['adj_close']}): {pct:.2f}%")
