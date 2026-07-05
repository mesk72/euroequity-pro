import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== stocks ===")
r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
    params={"select": "*", "ticker": "eq.SNDK"})
data = r.json()
print(data)

print("\n=== fundamentals ===")
r2 = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
    params={"select": "*", "ticker": "eq.SNDK"})
data2 = r2.json()
if isinstance(data2, list) and data2:
    for k, v in data2[0].items():
        print(f"  {k}: {v}")
else:
    print("  NESSUNA RIGA")
