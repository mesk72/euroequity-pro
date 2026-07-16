import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"*","ticker":"eq.ASML","exchange":"eq.AS"})
print("ASML fundamentals:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.ASML","exchange":"eq.AS","order":"date.desc","limit":"10"})
print("\nASML ultimi 10 prezzi grezzi:")
for row in r2.json():
    print(f"  {row}")
