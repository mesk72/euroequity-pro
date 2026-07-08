import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_count = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Prefer": "count=exact"}

EXCHANGES = [
    ("US", 3000), ("TSX", 400),
    ("LSE", None), ("XETRA", None), ("PA", None), ("OM", None), ("SWX", None),
    ("MIL", None), ("AS", 100), ("MC", 100), ("BR", 100), ("HE", 100),
    ("CPSE", 100), ("OB", 100), ("GR", 100), ("VI", None), ("IR", None), ("LS", None),
    ("TSE", 1000), ("SEHK", 500), ("ASX", 350), ("KRX", 400), ("SGX", 100),
]

print("=" * 60)
print("RIEPILOGO FINALE — WEEKEND REFRESH")
print("=" * 60)
print(f"{'Exchange':<10}{'in_universe':<15}{'Atteso':<10}{'Stato'}")
print("-" * 50)
problemi = []
for exch, atteso in EXCHANGES:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select": "ticker", "in_universe": "eq.true", "exchange": f"eq.{exch}", "limit": "1"})
    cr = r.headers.get("content-range", "")
    tot = cr.split("/")[-1] if "/" in cr else "?"
    stato = "OK"
    if atteso and tot.isdigit() and int(tot) < atteso * 0.9:
        stato = "SOTTO ATTESO"
        problemi.append(f"{exch}: {tot} (atteso ~{atteso})")
    print(f"{exch:<10}{tot:<15}{str(atteso or '-'):<10}{stato}")

print()
if problemi:
    print("ATTENZIONE — mercati sotto la soglia attesa:")
    for p in problemi:
        print(f"  - {p}")
else:
    print("Tutti i mercati sono in linea con le attese.")

print("\nFATTO.")
