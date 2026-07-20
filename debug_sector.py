import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Tutti i 19 titoli, con i ticker corretti trovati
portfolio = [
    ("BARC", "LSE", 6.85),
    ("ADBE", "US", 3.08),
    ("NWG", "LSE", 6.50),
    ("DBK", "XETRA", 5.31),
    ("ULVR", "LSE", 3.72),
    ("RKT", "LSE", 3.26),
    ("GRI", "LSE", 0.98),
    ("WKL", "AS", 4.77),
    ("IWG", "LSE", 3.81),
    ("1299", "SEHK", 1.04),
    ("GFC", "PA", 6.26),
    ("ITUB", "US", 6.37),  # confermato non coperto (Brasile)
    ("SHEL", "LSE", 6.76),
    ("VNA", "XETRA", 6.19),
    ("RI", "PA", 5.06),
    ("SAN", "PA", 6.31),
    ("CLNX", "MC", 6.05),
    ("RF", "PA", 6.61),
    ("KGX", "XETRA", 5.28),
]

found = []
not_found = []
total_weight_all = sum(p[2] for p in portfolio)

for ticker, exchange, weight in portfolio:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,value_score,growth_score,combined_rank","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}"})
    d = r.json()
    if d and d[0].get("value_score") is not None:
        found.append((ticker, exchange, weight, d[0]))
    else:
        not_found.append((ticker, exchange, weight))

covered_weight = sum(f[2] for f in found)
print(f"Peso totale portafoglio: {total_weight_all:.2f}%")
print(f"Peso coperto nel DB: {covered_weight:.2f}%")
print(f"Percentuale di copertura: {covered_weight/total_weight_all*100:.1f}%\n")

print("=== NON TROVATI (rimasti) ===")
for t, ex, w in not_found:
    print(f"  {t}.{ex} (peso {w}%)")

def weighted_avg(field):
    valid = [(f[3].get(field), f[2]) for f in found if f[3].get(field) is not None]
    if not valid: return None, 0
    wsum = sum(v*w for v,w in valid)
    wtot = sum(w for v,w in valid)
    return wsum/wtot, wtot

wv, wv_base = weighted_avg("value_score")
wg, wg_base = weighted_avg("growth_score")
wb, wb_base = weighted_avg("combined_rank")

print(f"\n=== MEDIE PESATE FINALI (18/19 titoli, {covered_weight:.2f}% del portafoglio) ===")
print(f"Value Score medio: {wv:.1f}")
print(f"Growth Score medio: {wg:.1f}")
print(f"Best Score medio: {wb:.1f}")
