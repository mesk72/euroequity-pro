import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
print(f"Status: {r.status_code} Righe: {len(r.text.splitlines())}")

reader = csv.DictReader(io.StringIO(r.text))
exchanges = {}
for row in reader:
    ex = row.get("Primary Exchange","").strip()
    country = row.get("Country","").strip()
    exchanges[ex] = exchanges.get(ex, {"count":0, "countries":set()})
    exchanges[ex]["count"] += 1
    exchanges[ex]["countries"].add(country)

print("\nExchange raw nel TIKR EU:")
for ex, info in sorted(exchanges.items(), key=lambda x: -x[1]["count"]):
    print(f"  {ex:<20} count={info['count']:>5} paesi={info['countries']}")
