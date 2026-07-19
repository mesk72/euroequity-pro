import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# ticker_originale, exchange_tentativo (ticker pulito, senza suffisso, nel nostro formato), peso%
portfolio = [
    ("PLTR", "US", 1.10),
    ("RHM", "XETRA", 1.17),
    ("MU", "US", 9.43),
    ("UBSG", "SWX", 2.31),
    ("JPM", "US", 1.42),
    ("TSM", "US", 8.84),
    ("NVDA", "US", 5.37),
    ("AAPL", "US", 1.21),
    ("ASML", "US", 1.96),
    ("GS", "US", 1.83),
    ("005930", "KRX", 1.20),  # Samsung
    ("RIOT", "US", 0.90),
    ("GOOGL", "US", 2.70),
    ("ASML", "AS", 3.08),
    ("META", "US", 2.35),
    ("NDA", "XETRA", 0.64),  # Aurubis
    ("ABBN", "SWX", 3.22),
    ("NKT", "CPSE", 1.09),
    ("FSLR", "US", 1.52),
    ("PGNY", "US", 0.74),
    ("B", "US", 2.72),  # Barrick, ticker B su NYSE
    ("1810", "SEHK", 0.39),  # Xiaomi
    ("VRTX", "US", 1.97),
    ("FORTUM", "OB", 0.56),  # incerto, Fortum e' finlandese non norvegese
    ("BOL", "OM", 1.58),  # Boliden e' svedese, OM
    ("MSFT", "US", 1.68),
    ("AMZN", "US", 1.37),
    ("ORK", "OB", 0.45),
    ("NBIX", "US", 1.81),
    ("FCX", "US", 3.21),
    ("INDA", "US", 1.29),  # ETF
    ("HST", "US", 2.61),
    ("NOC", "US", 0.56),
    ("EQT", "US", 2.96),
    ("AGRO", "US", 0.50),
    ("MC", "PA", 0.26),  # LVMH
    ("CDI", "PA", 0.92),  # Christian Dior
    ("NHY", "OB", 0.56),
    ("LMT", "US", 0.53),
    ("LDOS", "US", 0.66),
    ("D", "US", 1.32),
    ("SMT", "LSE", 0.64),  # Scottish Mortgage, investment trust
    ("SPY5", "LSE", 2.64),  # ETF
    ("NOC2", "US", 0.0),
    ("RL", "US", 0.32),
    ("VST", "US", 3.05),
    ("GAW", "LSE", 0.52),
    ("HAS", "US", 0.34),
    ("CNC", "US", 0.94),
    ("000660", "KRX", 0.53),  # SK Hynix
    ("BE", "US", 1.33),
    ("HO", "PA", 0.69),  # Thales
    ("AVAV", "US", 0.74),
    ("CEG", "US", 2.35),
    ("RRC", "US", 1.81),
    ("VALE", "US", 0.40),
    ("NOVO-B", "CPSE", 0.61),
    ("ETOR", "US", 0.25),
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
print(f"Peso totale analizzato: {total_weight_all:.2f}%")
print(f"Peso coperto nel DB (con score validi): {covered_weight:.2f}%")
print(f"Percentuale di copertura: {covered_weight/total_weight_all*100:.1f}%\n")

print("=== TROVATI ===")
for t, ex, w, d in found:
    print(f"  {t}.{ex} (peso {w}%): Value={d.get('value_score')}, Growth={d.get('growth_score')}, Best={d.get('combined_rank')}")

print("\n=== NON TROVATI ===")
for t, ex, w in not_found:
    print(f"  {t}.{ex} (peso {w}%)")

# Medie pesate — escludendo esplicitamente i None (2 titoli senza Growth/Best), non trattandoli come zero
def weighted_avg(field):
    valid = [(f[3].get(field), f[2]) for f in found if f[3].get(field) is not None]
    if not valid: return None, 0
    wsum = sum(v*w for v,w in valid)
    wtot = sum(w for v,w in valid)
    return wsum/wtot, wtot

wv, wv_base = weighted_avg("value_score")
wg, wg_base = weighted_avg("growth_score")
wb, wb_base = weighted_avg("combined_rank")

print(f"\n=== MEDIE PESATE (sul sotto-portafoglio coperto) ===")
print(f"Value Score medio: {wv:.1f} (base {wv_base:.2f}% di peso)")
print(f"Growth Score medio: {wg:.1f} (base {wg_base:.2f}% di peso, 2 titoli esclusi per dati mancanti)")
print(f"Best Score medio: {wb:.1f} (base {wb_base:.2f}% di peso, 2 titoli esclusi per dati mancanti)")
