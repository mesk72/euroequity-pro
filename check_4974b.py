import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

# Range esatto che daily_apac.py avrebbe usato: dal giorno dopo l'ultimo dato al 8 luglio
url = f"https://api.leeway.tech/api/v1/public/historicalquotes/4974.TSE?apitoken={LEEWAY_KEY}&from=2026-06-13&to=2026-07-08"
resp = requests.get(url, timeout=20)
print(f"Range 13/6-8/7: HTTP {resp.status_code}, body={resp.text[:600]}")

# Range piu' ampio per vedere fino a dove arrivano davvero i dati Leeway
url2 = f"https://api.leeway.tech/api/v1/public/historicalquotes/4974.TSE?apitoken={LEEWAY_KEY}&from=2026-05-01&to=2026-07-08"
resp2 = requests.get(url2, timeout=20)
data2 = resp2.json() if resp2.status_code == 200 else []
if isinstance(data2, list) and data2:
    print(f"Ultima data disponibile su Leeway per 4974.TSE: {data2[-1]['date']}")
    print(f"Totale righe 1 maggio - 8 luglio: {len(data2)}")
else:
    print("Nessun dato nel range esteso")
