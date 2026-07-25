import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type": "application/json"}

# Test la funzione RPC
r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/get_latest_two_prices", headers=headers_r,
    json={"exchange_list": ["US"]})
print("RPC status:", r.status_code)
data = r.json()
print("RPC righe restituite (campione):", data[:3] if isinstance(data, list) else data)
print("RPC totale righe:", len(data) if isinstance(data, list) else "N/A")

# Test la tabella sector_aggregates
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/sector_aggregates", headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}, params={"select":"*","limit":"1"})
print("\nTabella sector_aggregates status:", r2.status_code, r2.text[:200])
