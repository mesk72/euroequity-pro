import os, requests, json
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

all_rows = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"ticker,exchange,date,adj_close","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_rows.extend(batch)
    offset += 1000
    if offset % 50000 == 0:
        print(f"  ...{offset} righe scaricate")
    if len(batch) < 1000: break

print(f"Backup completato: {len(all_rows)} righe")
with open("prices_eod_backup.json", "w") as f:
    json.dump(all_rows, f)
print("Salvato in prices_eod_backup.json")
