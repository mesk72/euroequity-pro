import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for tk in ["7203", "9984"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{tk}","exchange":"eq.TSE","order":"date.desc","limit":"8"})
    print(f"{tk} ultime 8 righe:")
    for row in r.json():
        print(" ", row)
    print()
