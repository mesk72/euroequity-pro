import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Log per conferma numerica
r = requests.get(f"{SUPABASE_URL}/rest/v1/script_logs", headers=headers_r,
    params={"select":"log_text","script_name":"eq.daily_eu_yahoo","order":"created_at.desc","limit":"1"})
data = r.json()
if data:
    txt = data[0]["log_text"]
    for line in txt.split("\n"):
        if "Prezzi Yahoo" in line or "Rank EU" in line or "Combined rank" in line:
            print(line)

print()
for tk, ex in [("ASML","AS"), ("ROG","SWX"), ("SAP","XETRA"), ("MC","PA")]:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    print(f"{tk}.{ex}:", r2.json())
