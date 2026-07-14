import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/auth/v1/admin/users", headers=headers_r, params={"per_page": "50"})
data = r.json()
users = data.get("users", [])
print(f"Utenti totali trovati: {len(users)}")
print()
for u in sorted(users, key=lambda x: x.get("created_at","")):
    meta = u.get("user_metadata", {})
    print(f"ID: {u['id']}")
    print(f"  Email: {u.get('email')}")
    print(f"  Nome: {meta.get('name', '(nessuno)')}")
    print(f"  Paese: {meta.get('country', '(nessuno)')}")
    print(f"  Creato: {u.get('created_at')}")
    print(f"  Ultimo accesso: {u.get('last_sign_in_at')}")
    print()
