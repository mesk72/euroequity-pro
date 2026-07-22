import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"*","limit":"2"})
data = r.json()
if data:
    print("Colonne disponibili:", sorted(data[0].keys()))
    print("\nEsempio riga:", data[0])
else:
    print("Nessuna riga o errore:", data)
