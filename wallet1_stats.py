import os, requests, statistics
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

USER_ID = "fee79b7f-1481-4936-b381-4c28cf832414"

r = requests.get(f"{SUPABASE_URL}/rest/v1/watchlist", headers=headers_r,
    params={"select":"ticker,exchange,wallet","user_id":f"eq.{USER_ID}"})
all_wallets = r.json()
print(f"Righe totali per questo utente: {len(all_wallets)}")
from collections import Counter
by_wallet = Counter(w.get("wallet") for w in all_wallets)
print("Distribuzione per wallet:", dict(by_wallet))

wallet1 = [w for w in all_wallets if w.get("wallet") == 0]
print(f"\nWallet 1 (wallet=0): {len(wallet1)} titoli")
for w in wallet1:
    print(f"  {w['ticker']}.{w['exchange']}")
