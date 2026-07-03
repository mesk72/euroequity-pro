import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
             "Prefer": "count=exact"}

EX_MAP = {
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "ARCA":"US","OTCPK":"US","NYSEAM":"US",
    "TSX":"TSX","TSXV":"TSX","CNSX":"TSX","NEOE":"TSX",
    "MutualFund": None,
}

# Conta US in_universe nel DB
for exchange in ["US", "TSX"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":f"eq.{exchange}",
                "in_universe":"eq.true","limit":"1"})
    count = int(r.headers.get("content-range","0/0").split("/")[-1])
    print(f"{exchange}: in_universe={count}")

# Conta titoli nel TIKR NA per exchange
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv",
    headers={"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY})
reader = csv.DictReader(io.StringIO(r.text))
counts = {}
not_mapped = {}
for row in reader:
    ex_raw = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw)
    if exchange:
        counts[exchange] = counts.get(exchange, 0) + 1
    else:
        not_mapped[ex_raw] = not_mapped.get(ex_raw, 0) + 1

print(f"\nNel TIKR NA:")
for ex, c in sorted(counts.items()):
    print(f"  {ex}: {c}")
print(f"Non mappati: {not_mapped}")
