import os, requests, sys
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

results = []
for ex in ALL_RANKED:
    try:
        rd = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","exchange":f"eq.{ex}","order":"date.desc","limit":"1"}, timeout=10)
        newest = rd.json()
        newest_date = newest[0]["date"] if newest else "NESSUN DATO"
    except Exception as e:
        newest_date = f"ERRORE: {e}"
    results.append(f"{ex}: {newest_date}")

with open("minimal_check_result.txt", "w") as f:
    f.write("\n".join(results))
print("FATTO — scritto in minimal_check_result.txt")
for line in results:
    print(line)
