import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Log completo
r = requests.get(f"{SUPABASE_URL}/rest/v1/script_logs", headers=headers_r,
    params={"select":"log_text,created_at","script_name":"eq.daily_apac_yahoo","order":"created_at.desc","limit":"1"})
data = r.json()
print("=== LOG COMPLETO ===")
if data:
    print(data[0]["log_text"])
print()

# Campione ampio di titoli, inclusi quelli storicamente problematici
print("=== CAMPIONE PREZZI (20 titoli casuali + i 3 storicamente problematici) ===")
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange","in_universe":"eq.true","exchange":"in.(TSE,SEHK,ASX)","limit":"20"})
sample = [(s["ticker"], s["exchange"]) for s in r2.json()]
sample += [("7203","TSE"), ("9984","TSE"), ("BHP","ASX")]

dates_seen = {}
for tk, ex in sample:
    r3 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{tk}","exchange":f"eq.{ex}","order":"date.desc","limit":"1"})
    d = r3.json()
    date_val = d[0]["date"] if d else "NESSUNO"
    dates_seen[date_val] = dates_seen.get(date_val, 0) + 1
    marker = " <-- storicamente problematico" if tk in ("7203","9984","BHP") else ""
    print(f"  {tk}.{ex}: {date_val}{marker}")

print(f"\nRiepilogo date: {dates_seen}")
