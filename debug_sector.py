import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Verifica se esiste gia' una tabella sector_aggregates e la sua struttura
r = requests.get(f"{SUPABASE_URL}/rest/v1/sector_aggregates", headers=headers_r, params={"select":"*","limit":"3"})
print("sector_aggregates esiste?", r.status_code)
if r.status_code == 200:
    print("Contenuto campione:", r.json())
