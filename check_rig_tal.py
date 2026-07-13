import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
text = r.content.decode('utf-8', errors='replace')
reader = csv.DictReader(io.StringIO(text))

for target in ['RIG', 'TAL']:
    print(f"\n=== {target} nel file TIKR (tutte le righe) ===")
    f2 = io.StringIO(text)
    reader2 = csv.DictReader(f2)
    for row in reader2:
        if row.get('Ticker','').strip().upper() == target:
            print(f"  {row.get('Ticker')} | {row.get('Company Name')} | {row.get('Primary Exchange')} | {row.get('Country')} | MktCap={row.get('Last Mkt Cap')} | P/B={row.get('LTM P/BVPS LTM')}")

for target, exch in [('RIG','US'), ('TAL','US')]:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mkt_cap,pb","ticker":f"eq.{target}","exchange":f"eq.{exch}"})
    print(f"\n{target}.{exch} nel database:", r2.json())
