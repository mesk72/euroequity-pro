import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for tk in ["AAC","AOV","CCP","EDV","WES"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":"eq.ASX","order":"date.desc","limit":"3000"})
    rows = r.json()
    dates = [row["date"] for row in rows]
    dupes = {d:c for d,c in Counter(dates).items() if c > 1}
    print(f"{tk}: {len(rows)} righe totali, {len(set(dates))} date distinte, duplicati: {len(dupes)} date con piu' righe" + (f" es: {list(dupes.items())[:5]}" if dupes else ""))
