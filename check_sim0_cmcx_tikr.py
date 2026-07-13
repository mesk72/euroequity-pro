import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Database
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","ticker":"eq.SIM0"})
print("SIM0 nel database (stocks):", r.json())
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,mom1w,mom1m,pe_trailing","ticker":"eq.SIM0"})
print("SIM0 nel database (fundamentals):", r2.json())

# File TIKR EU grezzo
r3 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv", headers=headers_r)
text = r3.content.decode('utf-8', errors='replace')
reader = csv.DictReader(io.StringIO(text))
print("\n=== Righe TIKR EU per SIM0 e CMCX ===")
for row in reader:
    t = row.get('Ticker','').strip().upper()
    if t in ('SIM0', 'CMCX'):
        print(f"  {t} | {row.get('Company Name')} | {row.get('Primary Exchange')} | {row.get('Country')} | MktCap={row.get('Last Mkt Cap')} | P/E LTM={row.get('LTM P/E LTM')}")
