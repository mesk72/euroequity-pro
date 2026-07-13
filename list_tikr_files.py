import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type": "application/json"}
r = requests.post(f"{SUPABASE_URL}/storage/v1/object/list/tikr-uploads", headers=headers, json={"prefix": "", "limit": 200})
print("STATUS:", r.status_code)
for item in r.json():
    print(f"  {item.get('name')} - {item.get('metadata', {}).get('size', '?')} bytes - {item.get('updated_at', '?')}")
