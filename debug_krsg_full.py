import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for exch in ["KRX", "SGX"]:
    print(f"=== {exch} ===")
    # Conteggio in_universe=true reale, in blocco
    total = 0
    offset = 0
    while True:
        r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
            params={"select": "ticker", "in_universe": "eq.true", "exchange": f"eq.{exch}",
                    "offset": str(offset), "limit": "1000"})
        data = r.json()
        if not isinstance(data, list) or not data: break
        total += len(data)
        offset += 1000
        if len(data) < 1000: break
    print(f"  in_universe=true reale: {total}")

    # Alcuni esempi di fundamentals per vedere i rank
    r2 = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker,mkt_cap,value_score,growth_score,combined_rank,pe_forward,eps_growth",
                "exchange": f"eq.{exch}", "limit": "5", "order": "mkt_cap.desc"})
    data2 = r2.json()
    print(f"  Esempi fundamentals (top 5 per mkt_cap):")
    if isinstance(data2, list):
        for row in data2:
            print(f"    {row}")

    # Conteggio fundamentals totali per questo exchange
    r3 = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "ticker", "exchange": f"eq.{exch}", "limit": "1000"})
    data3 = r3.json()
    print(f"  Righe fundamentals totali (max 1000 mostrate): {len(data3) if isinstance(data3, list) else 'ERRORE'}")
    print()
