import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

tickers = ["A005930", "A000660", "005930", "000660"]  # con e senza prefisso A, per sicurezza

for t in tickers:
    print(f"=== stocks: ticker={t} ===")
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "*", "ticker": f"eq.{t}", "exchange": "eq.KRX"})
    data = r.json()
    print(data if data else "  NESSUNA RIGA")

    print(f"=== fundamentals: ticker={t} ===")
    r2 = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
        params={"select": "*", "ticker": f"eq.{t}", "exchange": "eq.KRX"})
    data2 = r2.json()
    if isinstance(data2, list) and data2:
        for k, v in data2[0].items():
            print(f"  {k}: {v}")
    else:
        print("  NESSUNA RIGA")
    print()

# Conto quanti titoli KRX in fundamentals hanno mkt_cap NON nullo
print("=== Conteggio KRX con mkt_cap non nullo ===")
r3 = requests.get(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_r,
    params={"select": "ticker,mkt_cap,combined_rank", "exchange": "eq.KRX",
            "mkt_cap": "not.is.null", "limit": "10"})
print(r3.json())
