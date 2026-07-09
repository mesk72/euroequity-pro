import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# 1. Trova SK Hynix nell'universo KRX
r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company","exchange":"eq.KRX","company":"ilike.*Hynix*"})
print("SK Hynix trovato:", r.json())
hynix_rows = r.json()

for row in hynix_rows:
    t, ex = row["ticker"], row["exchange"]
    rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{t}","exchange":f"eq.{ex}","order":"date.desc","limit":"10"})
    print(f"\nUltimi 10 prezzi {t}.{ex}:")
    for p in rp.json():
        print(" ", p)

print("\n" + "="*50)
print("J36 Singapore - dati grezzi TIKR")
print("="*50)
r2 = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r2.text))
for row in reader:
    if row.get("Ticker","").strip() == "J36":
        for k in ["Company Name","EPS Normalized (FY 2025)","Mean EPS Normalized (FY 2026)",
                   "Mean EPS Normalized (FY 2027)","Mean EPS Normalized (FY 2028)",
                   "EPS (GAAP) (FY 2025)","Mean EPS (GAAP) (FY 2026)",
                   "Mean EPS (GAAP) (FY 2027)","Mean EPS (GAAP) (FY 2028)"]:
            print(f"  {k}: {row.get(k)!r}")
        break
else:
    print("J36 non trovato nel file TIKR")
