import os, requests
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/watchlist", headers=headers_r,
    params={"select":"user_id,wallet"})
data = r.json()
print(f"Righe totali in watchlist: {len(data)}")

by_user = Counter(d.get("user_id") for d in data)
print(f"\nUtenti distinti con almeno una riga: {len(by_user)}")
for uid, count in by_user.most_common():
    print(f"  user_id={uid}: {count} righe totali (tutti i wallet)")

# Controlla anche l'utente Andrea specificamente
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/auth.users" if False else f"{SUPABASE_URL}/rest/v1/watchlist", headers=headers_r,
    params={"select":"user_id"})
