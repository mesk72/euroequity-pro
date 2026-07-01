import os, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
             "Prefer": "count=exact"}

# Date aggiornamento prezzi attese
PRICE_DATES = {
    "TSE": "2026-07-01", "SEHK": "2026-07-01", "ASX": "2026-07-01",
    "KRX": "2026-07-01", "SGX": "2026-07-01",
    "MIL": "2026-06-30", "XETRA": "2026-06-30", "PA": "2026-06-30",
    "LSE": "2026-06-30", "OM": "2026-06-30", "SWX": "2026-06-30",
    "OB": "2026-06-30", "AS": "2026-06-30", "MC": "2026-06-30",
    "BR": "2026-06-30", "CPSE": "2026-06-30", "HE": "2026-06-30",
    "VI": "2026-06-30", "IR": "2026-06-30", "LS": "2026-06-30",
    "US": "2026-06-30", "TSX": "2026-06-30",
}

ALL_EXCHANGES = [
    ("MIL","EU"),("XETRA","EU"),("PA","EU"),("LSE","EU"),
    ("OM","EU"),("SWX","EU"),("OB","EU"),("AS","EU"),
    ("MC","EU"),("BR","EU"),("CPSE","EU"),("HE","EU"),
    ("VI","EU"),("IR","EU"),("LS","EU"),
    ("US","NA"),("TSX","NA"),
    ("TSE","APAC"),("SEHK","APAC"),("ASX","APAC"),
    ("KRX","APAC"),("SGX","APAC"),
]

print("=== UNIVERSO ATTUALE CON PREZZI ===")
print(f"{'Exchange':<8} {'Region':<6} {'In Universe':>12} {'Con Prezzi':>11} {'% OK':>6} {'Ultima data attesa'}")
print("-" * 70)

total = {"EU":{"univ":0,"price":0}, "NA":{"univ":0,"price":0}, "APAC":{"univ":0,"price":0}}

for exchange, region in ALL_EXCHANGES:
    # Conta in_universe
    r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{exchange}",
                "in_universe":"eq.true","limit":"1"})
    n_univ = int(r1.headers.get("content-range","0/0").split("/")[-1])

    # Conta con prezzi aggiornati alla data attesa
    expected_date = PRICE_DATES.get(exchange, "2026-06-30")
    min_date = (datetime.strptime(expected_date, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
    
    # Carica ticker in universe
    tickers_univ = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY},
            params={"select":"ticker","exchange":f"eq.{exchange}",
                    "in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        tickers_univ.extend([s["ticker"] for s in batch])
        offset += 1000
        if len(batch)<1000: break

    # Carica ticker con prezzi recenti (bulk)
    tickers_price = set()
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod",
            headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY},
            params={"select":"ticker","exchange":f"eq.{exchange}",
                    "date":f"gte.{min_date}",
                    "order":"ticker.asc","limit":"2000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for row in batch: tickers_price.add(row["ticker"])
        offset += 2000
        if len(batch)<2000: break

    n_price = sum(1 for t in tickers_univ if t in tickers_price)
    pct = round(n_price/n_univ*100) if n_univ > 0 else 0
    
    print(f"  {exchange:<8} {region:<6} {n_univ:>12} {n_price:>11} {pct:>5}% {expected_date}")
    total[region]["univ"] += n_univ
    total[region]["price"] += n_price

print("-" * 70)
for region, v in total.items():
    pct = round(v["price"]/v["univ"]*100) if v["univ"] > 0 else 0
    print(f"  {'TOTALE '+region:<14} {v['univ']:>12} {v['price']:>11} {pct:>5}%")
grand_univ = sum(v["univ"] for v in total.values())
grand_price = sum(v["price"] for v in total.values())
print(f"  {'TOTALE GLOBALE':<14} {grand_univ:>12} {grand_price:>11} {round(grand_price/grand_univ*100) if grand_univ>0 else 0:>5}%")
