import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Verifica se esiste gia' una funzione RPC generica per eseguire SQL
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type": "application/json"}
r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/exec_sql", headers=headers_r,
    json={"query": "SELECT 1"})
print("Test rpc/exec_sql:", r.status_code, r.text[:300])
