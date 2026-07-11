import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_c = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

# Conteggio efficiente: HEAD-style, nessun dato scaricato, solo il count esatto
r = requests.head(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_c,
    params={"exchange":"eq.US","date":"eq.2026-07-10"}, timeout=30)
print("Righe US al 10 luglio (count esatto, HEAD):", r.headers.get("content-range"), "HTTP", r.status_code)

r2 = requests.head(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_c,
    params={"exchange":"eq.US","in_universe":"eq.true"}, timeout=30)
print("Universo US totale:", r2.headers.get("content-range"))
