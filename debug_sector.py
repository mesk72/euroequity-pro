import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

portfolio = [
    ("BAC","US",7.44), ("JPM","US",7.19), ("GS","US",6.86), ("C","US",6.34),
    ("AMD","US",10.75), ("NVDA","US",6.45), ("RR.","LSE",4.84), ("AMZN","US",3.22),
    ("MU","US",11.91), ("GOOGL","US",3.12), ("IAG","LSE",2.50), ("KLAC","US",11.74),
    ("CAT","US",6.61), ("INTC","US",11.02),
]

results = []
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
            "ticker": ticker, "weight": weight, "company": s.get("company"),
            "sector": s.get("sector"), "country": s.get("country"),
            "value_score": f.get("value_score"), "growth_score": f.get("growth_score"),
            "best_score": f.get("combined_rank"),
        })

print(f"Coperti: {len(results)}/14\n")

total_weight = sum(r["weight"] for r in results)
print(f"Peso totale coperto: {total_weight:.2f}%  (ribilanciato su questo totale)\n")

wavg_value = sum(r["value_score"] * r["weight"] for r in results) / total_weight
wavg_growth = sum(r["growth_score"] * r["weight"] for r in results) / total_weight
wavg_best = sum(r["best_score"] * r["weight"] for r in results) / total_weight
print(f"Weighted Avg Value Score:  {wavg_value:.2f}")
print(f"Weighted Avg Growth Score: {wavg_growth:.2f}")
print(f"Weighted Avg Best Score:   {wavg_best:.2f}\n")

sector_w = {}
for r in results:
    sector_w[r["sector"]] = sector_w.get(r["sector"], 0) + r["weight"] / total_weight * 100
print("Sector allocation (ribilanciato):")
for sec, w in sorted(sector_w.items(), key=lambda x: -x[1]):
    print(f"  {sec}: {w:.2f}%")

country_w = {}
for r in results:
    country_w[r["country"]] = country_w.get(r["country"], 0) + r["weight"] / total_weight * 100
print("\nCountry allocation (ribilanciato):")
for c, w in sorted(country_w.items(), key=lambda x: -x[1]):
    print(f"  {c}: {w:.2f}%")
