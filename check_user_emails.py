import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

USER_ID = "fee79b7f-1481-4936-b381-4c28cf832414"
r = requests.get(f"{SUPABASE_URL}/auth/v1/admin/users/{USER_ID}", headers=headers_r)
print("STATUS:", r.status_code)
print(r.text)
