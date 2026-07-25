import os, requests, time
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type": "application/json"}

start = time.time()
r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/get_latest_two_prices", headers=headers_r,
    json={"exchange_list": ["US"]}, timeout=30)
elapsed = time.time() - start
print("RPC status:", r.status_code, f"tempo: {elapsed:.2f}s")
data = r.json()
if isinstance(data, list):
    print("Righe restituite:", len(data))
    print("Campione:", data[:3])
else:
    print("Errore:", data)
