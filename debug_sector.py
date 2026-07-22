import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ALL_RANKED = ['MIL','XETRA','PA','AS','MC','BR','LS','VI','HE','IR','GR','LSE','SWX','OM','OB','CPSE','NGM','TSE','SEHK','TSX','ASX','KRX','SGX','US']

for ex in ALL_RANKED:
    r = requests.delete(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"exchange": f"eq.{ex}"})
    print(f"{ex}: HTTP {r.status_code}")
