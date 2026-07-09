import os, requests, datetime
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

# Conferma che la riga di test appena scritta si trovi
r0 = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"ticker,fetched_at","ticker":"eq.TESTXYZ"})
print("Riga di test trovata:", r0.json())

# Prova il filtro temporale con formato esplicito UTC con 'Z'
one_hour_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"ticker","fetched_at":f"gte.{one_hour_ago}","limit":"1"})
print(f"Filtro '{one_hour_ago}': Content-Range={r2.headers.get('content-range')}  status={r2.status_code}")
if r2.status_code != 200:
    print("  Errore:", r2.text[:300])

# Controlla il valore fetched_at massimo attuale nella tabella
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/news_cache", headers=headers_r,
    params={"select":"ticker,fetched_at","order":"fetched_at.desc","limit":"3"})
print("Righe piu' recenti:", r3.json())
