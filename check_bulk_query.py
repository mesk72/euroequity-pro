import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
    params={"select": "ticker,date", "exchange": "eq.LSE",
            "order": "ticker.asc,date.desc", "limit": "10", "offset": "0"})
print("Status:", r.status_code)
print("Body:", r.text[:1000])
