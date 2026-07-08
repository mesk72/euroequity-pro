import os, requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

# Exchange: (target atteso o None, max giorni di eta' prezzo accettabili)
# 2 giorni di tolleranza copre weekend/festivi senza nascondere problemi reali.
EXCHANGES = {
    "US": 3000, "TSX": 400,
    "LSE": None, "XETRA": None, "PA": None, "OM": None, "SWX": None, "MIL": None,
    "AS": 100, "MC": 100, "BR": 100, "HE": 100, "CPSE": 100, "OB": 100, "GR": 100,
    "VI": None, "IR": None, "LS": None,
    "TSE": 1000, "SEHK": 500, "ASX": 350, "KRX": 400, "SGX": 100,
}
MAX_STALE_DAYS = 4  # tollera weekend + un giorno di margine

today = datetime.now().date()
righe = []
problemi = []

for exch, target in EXCHANGES.items():
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "in_universe": "eq.true", "exchange": f"eq.{exch}", "limit": "1"})
    cr = r.headers.get("content-range", "")
    count = int(cr.split("/")[-1]) if "/" in cr and cr.split("/")[-1].isdigit() else 0

    # Campione di 20 titoli in_universe: quanti hanno un prezzo recente
    rs = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker", "in_universe": "eq.true", "exchange": f"eq.{exch}", "limit": "20"})
    sample = [s["ticker"] for s in rs.json()] if isinstance(rs.json(), list) else []
    fresh = 0
    oldest_seen = None
    for t in sample:
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select": "date", "ticker": f"eq.{t}", "exchange": f"eq.{exch}",
                     "order": "date.desc", "limit": "1"})
        d = rp.json()
        if isinstance(d, list) and d:
            pdate = datetime.strptime(d[0]["date"], "%Y-%m-%d").date()
            age = (today - pdate).days
            if oldest_seen is None or age > oldest_seen: oldest_seen = age
            if age <= MAX_STALE_DAYS: fresh += 1

    count_ok = (target is None) or (count >= target * 0.95)
    fresh_ok = len(sample) == 0 or (fresh / len(sample)) >= 0.9
    status = "OK" if (count_ok and fresh_ok) else "PROBLEMA"
    if status == "PROBLEMA":
        problemi.append(f"{exch}: count={count}/{target or '-'} fresh={fresh}/{len(sample)} eta_max={oldest_seen}gg")

    righe.append(f"{exch:8} count={count:5}/{str(target or '-'):5}  campione_fresco={fresh}/{len(sample)}  eta_max_campione={oldest_seen if oldest_seen is not None else '-'}gg  [{status}]")

print("=" * 70)
print(f"HEALTH CHECK — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 70)
for riga in righe:
    print(riga)
print("-" * 70)
if problemi:
    print(f"STATO GENERALE: PROBLEMA ({len(problemi)} mercati)")
    for p in problemi:
        print(f"  - {p}")
else:
    print("STATO GENERALE: TUTTO OK")
print("=" * 70)
