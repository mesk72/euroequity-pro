import os, requests, json
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

# Conta prima quante righe ci sono in totale, per sapere cosa aspettarci
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r, params={"select":"ticker","limit":"1"})
total = r.headers.get("content-range","").split("/")[-1]
print(f"Righe totali da salvare: {total}")

# Backup a blocchi, salvato come file compresso per non superare limiti di dimensione
all_rows = []
offset = 0
headers_plain = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_plain,
        params={"select":"ticker,exchange,date,adj_close","limit":"5000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_rows.extend(batch)
    offset += 5000
    if offset % 50000 == 0:
        print(f"  ...{offset} righe scaricate")
    if len(batch) < 5000: break

print(f"Backup completato: {len(all_rows)} righe")
with open("prices_eod_backup.json", "w") as f:
    json.dump(all_rows, f)
print("Salvato in prices_eod_backup.json")
