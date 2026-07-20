import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Riprovo con ticker del mercato primario (Londra), non ADR USA
retry_list = [
    ("BARC", "LSE", "Barclays"),
    ("NWG", "LSE", "NatWest"),
    ("ULVR", "LSE", "Unilever"),
    ("SHEL", "LSE", "Shell"),
]

for ticker, exchange, name in retry_list:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,value_score,growth_score,combined_rank","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
    d = r.json()
    if d and d[0].get("value_score") is not None:
        print(f"TROVATO {name} ({ticker}.{exchange}): Value={d[0].get('value_score')}, Growth={d[0].get('growth_score')}, Best={d[0].get('combined_rank')}")
    else:
        print(f"NON TROVATO {name} ({ticker}.{exchange})")

# Itau - cerca per nome, dato che non sappiamo se copriamo il Brasile
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","company":"ilike.*itau*","limit":"10"})
print("\nRicerca Itau per nome:", r2.json())
