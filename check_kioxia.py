import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.285A","exchange":"eq.TSE","order":"date.desc","limit":"20"})
print("Kioxia ultimi 20 prezzi:")
for row in r.json():
    print(f"  {row}")
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.285A","exchange":"eq.TSE","date":"gte.2025-07-01","date2":"lte.2025-07-15","order":"date.asc","limit":"10"})
print("\nKioxia intorno a un anno fa:")
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.285A","exchange":"eq.TSE","date":"gte.2025-07-01","order":"date.asc","limit":"10"})
for row in r3.json():
    print(f"  {row}")
