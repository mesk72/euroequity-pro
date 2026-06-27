import os, requests
from collections import Counter

SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
headers_r    = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Leggi TUTTI i campi della tabella stocks per capire cosa c'è
r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
    params={"select": "*", "exchange": "eq.US", "in_universe": "eq.true", "limit": "5"})
data = r.json()
if isinstance(data, list) and data:
    print("Campi tabella stocks:")
    print(list(data[0].keys()))
    print()
    for d in data:
        print(d)

# Leggi anche da fundamentals per vedere se c'è exchange_sub o listing_exchange
r2 = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
    params={"select": "*", "exchange": "eq.US", "limit": "3"})
data2 = r2.json()
if isinstance(data2, list) and data2:
    print("\nCampi tabella fundamentals:")
    print(list(data2[0].keys()))
