import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

dow = [
    ("GS", 12.13), ("CAT", 10.02), ("UNH", 4.85), ("MSFT", 4.48), ("TRV", 4.20),
    ("AMGN", 4.17), ("V", 4.08), ("AXP", 4.04), ("GOOGL", 3.95), ("JPM", 3.88),
    ("HD", 3.86), ("AAPL", 3.80), ("SHW", 3.77), ("MCD", 3.04), ("JNJ", 2.88),
    ("AMZN", 2.82), ("HON", 2.56), ("BA", 2.43), ("IBM", 2.42), ("NVDA", 2.31),
    ("CVX", 2.14), ("CRM", 1.95), ("MMM", 1.82), ("PG", 1.71), ("MRK", 1.45),
    ("WMT", 1.30), ("CSCO", 1.28), ("DIS", 1.11), ("KO", 0.93), ("NKE", 0.50),
]

print(f"Somma pesi forniti: {sum(w for _,w in dow):.2f}%\n")

found = []
not_found = []
for ticker, weight in dow:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,implied_growth_10y","ticker":f"eq.{ticker}","exchange":"eq.US"})
    d = r.json()
    if d and d[0].get("implied_growth_10y") is not None:
        found.append((ticker, weight, d[0]["implied_growth_10y"]))
    else:
        not_found.append((ticker, weight))

print("=== TROVATI ===")
for t, w, ig in found:
    print(f"  {t} (peso {w}%): Implied Growth = {round(ig*100,2)}%")

print("\n=== NON TROVATI ===")
for t, w in not_found:
    print(f"  {t} (peso {w}%)")

covered_weight = sum(w for _,w,_ in found)
wsum = sum(ig * w for _,w,ig in found)
weighted_avg = wsum / covered_weight if covered_weight > 0 else None

print(f"\nPeso coperto: {covered_weight:.2f}% su {sum(w for _,w in dow):.2f}% totale")
if weighted_avg is not None:
    print(f"IMPLIED GROWTH MEDIO PESATO (Dow Jones): {round(weighted_avg*100, 2)}%")
