import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Tentativo 1: schema auth via REST diretto (di solito non esposto)
r = requests.get(f"{SUPABASE_URL}/rest/v1/users", headers=headers_r, params={"select":"*"})
print("Tentativo /rest/v1/users:", r.status_code, r.text[:300])

# Tentativo 2: Admin API di Supabase Auth (endpoint diverso, stesso service key)
r2 = requests.get(f"{SUPABASE_URL}/auth/v1/admin/users", headers={**headers_r, "apikey": SERVICE_KEY})
print("\nTentativo /auth/v1/admin/users:", r2.status_code)
print(r2.text[:1500])

# Tentativo 3: tabella "profiles" se esiste
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/profiles", headers=headers_r, params={"select":"*"})
print("\nTentativo /rest/v1/profiles:", r3.status_code, r3.text[:300])
