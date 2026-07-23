import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Verifica diretta nel DB: AAPL ha i rank sorgente popolati?
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,rank_pe_ltm,rank_pe_ntm,rank_pb,rank_eps_gr,rank_rev_gr","ticker":"eq.AAPL","exchange":"eq.US"})
print("AAPL rank sorgente nel DB:", r.json())
