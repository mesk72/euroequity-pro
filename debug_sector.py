import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type": "application/json"}

# Marca in_universe=false per i titoli sempre esclusi ma ancora attivi, e 1COV (delistato confermato)
to_exclude = [
    ("YATO","MC"), ("COL","MC"), ("YCPS","MC"), ("SCHLR","MC"), ("YZBL","MC"),
    ("YTST","MC"), ("YFID","MC"), ("YHTI","MC"), ("SCHST","MC"), ("YVIV","MC"), ("YEPSA","MC"),
    ("MLMTP","PA"), ("G6M","ASX"),
    ("1COV","XETRA"),  # Covestro, delistata/acquisita, confermato Yahoo vuoto
]
for tk, ex in to_exclude:
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
        params={"ticker": f"eq.{tk}", "exchange": f"eq.{ex}"},
        json={"in_universe": False})
    print(f"{tk}.{ex}: HTTP {r.status_code}")
