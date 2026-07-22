import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# ticker, exchange (RR.L e IAG.L sono LSE), peso %
portfolio = [
    ("BAC","US",7.44), ("JPM","US",7.19), ("GS","US",6.86), ("C","US",6.34),
    ("AMD","US",10.75), ("NVDA","US",6.45), ("RR","LSE",4.84), ("AMZN","US",3.22),
    ("MU","US",11.91), ("GOOG","US",3.12), ("IAG","LSE",2.50), ("KLAC","US",11.74),
    ("CAT","US",6.61), ("INTC","US",11.02),
]

results = []
not_found = []
for ticker, exchange, weight in portfolio:
    rs = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange,company,sector,country","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
    sdata = rs.json()
    rf = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"value_score,growth_score,combined_rank","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
    fdata = rf.json()
    if sdata and fdata:
        s, f = sdata[0], fdata[0]
        results.append({
            "ticker": ticker, "exchange": exchange, "weight": weight,
            "company": s.get("company"), "sector": s.get("sector"), "country": s.get("country"),
            "value_score": f.get("value_score"), "growth_score": f.get("growth_score"),
            "best_score": f.get("combined_rank"),
        })
    else:
        not_found.append((ticker, exchange, weight))

print(f"Trovati: {len(results)}/14")
print(f"Non trovati: {not_found}")
print()
for r in results:
    print(r)
