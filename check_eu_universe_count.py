import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker","in_universe":"eq.true","exchange":"in.(MIL,PA,XETRA,LSE,OM,OB,SWX,MC,AS,HE,BR,GR,CPSE,VI,LS,IR)","limit":"1"})
print("Content-Range:", r.headers.get("content-range"))
