import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Leggi UN titolo da stocks con tutte le colonne
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"*", "exchange":"eq.MIL", "limit":"1"})
print(f"Status: {r.status_code}")
data = r.json()
if isinstance(data, list) and data:
    print("Colonne stocks:")
    for k, v in data[0].items():
        print(f"  {k}: {v}")
else:
    print(f"Errore: {r.text[:300]}")

# Stessa cosa per fundamentals
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"*", "exchange":"eq.MIL", "limit":"1"})
data2 = r2.json()
if isinstance(data2, list) and data2:
    print("\nColonne fundamentals:")
    for k, v in data2[0].items():
        print(f"  {k}: {v}")
