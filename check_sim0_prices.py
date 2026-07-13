import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.SIM0","exchange":"eq.XETRA","order":"date.desc","limit":"30"})
print("SIM0.XETRA prezzi grezzi (piu' recenti in cima):")
for row in r.json():
    print(f"  {row}")
