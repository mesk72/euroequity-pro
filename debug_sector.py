import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"*","ticker":"eq.NVDA","exchange":"eq.US"})
data = r.json()
if data:
    print("Colonne disponibili in fundamentals per NVDA:")
    for k in sorted(data[0].keys()):
        if 'sect' in k.lower() or 'indus' in k.lower():
            print(f"  >>> {k}: {data[0][k]}")
    print("\nTutte le colonne:", sorted(data[0].keys()))

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"*","ticker":"eq.NVDA","exchange":"eq.US"})
data2 = r2.json()
if data2:
    print("\nColonne disponibili in stocks per NVDA:")
    for k in sorted(data2[0].keys()):
        if 'sect' in k.lower() or 'indus' in k.lower():
            print(f"  >>> {k}: {data2[0][k]}")
