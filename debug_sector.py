import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type":"application/json", "Prefer":"return=representation"}

r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks?ticker=eq.NOVO%20B&exchange=eq.CPSE",
    headers=headers_up, json={"in_universe": True})
print("Update result:", r.status_code, r.json())
