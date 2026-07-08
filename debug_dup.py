import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer":"count=exact"}

for t, ex in [("1305","TSE"),("1","SEHK"),("360","ASX")]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"*","ticker":f"eq.{t}","exchange":f"eq.{ex}"})
    print(f"{t}.{ex} -> HTTP {r.status_code} righe={r.headers.get('content-range')}")
    for row in r.json():
        print("  ", row)
print()
# controlla anche gli header up usati dagli script per capire il merge target
print("Controllo constraint: provo un upsert di test su un ticker fittizio")
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=representation"}
r = requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_up,
    json=[{"ticker":"TESTXYZ","exchange":"TSE","mkt_cap":12345.67}])
print("upsert test ->", r.status_code, r.text[:300])
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"*","ticker":"eq.TESTXYZ","exchange":"eq.TSE"})
print("verifica ->", r2.status_code, r2.json())
# ripulisci
requests.delete(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"ticker":"eq.TESTXYZ","exchange":"eq.TSE"})
