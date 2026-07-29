import os, requests, re
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY, "Content-Type": "application/json"}

fixed = 0

# TSX .UN: CAR.UN.TO -> CAR-UN.TO
rs = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,yahoo_ticker","exchange":"eq.TSX","ticker":"like.*.UN"})
for s in rs.json():
    yt = s.get("yahoo_ticker") or ""
    if ".UN.TO" in yt:
        new_yt = yt.replace(".UN.TO", "-UN.TO")
        rp = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
            params={"ticker": f"eq.{s['ticker']}", "exchange": "eq.TSX"},
            json={"yahoo_ticker": new_yt})
        if rp.status_code in (200,204): fixed += 1
        print(f"TSX {s['ticker']}: {yt} -> {new_yt} [{rp.status_code}]")

# KRX A0xxxxx: A000250.KS -> 000250.KS
rs2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,yahoo_ticker","exchange":"eq.KRX","ticker":"like.A*"})
for s in rs2.json():
    yt = s.get("yahoo_ticker") or ""
    m = re.match(r"^A(\d+\.K[SQ])$", yt)
    if m:
        new_yt = m.group(1)
        rp = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
            params={"ticker": f"eq.{s['ticker']}", "exchange": "eq.KRX"},
            json={"yahoo_ticker": new_yt})
        if rp.status_code in (200,204): fixed += 1
        print(f"KRX {s['ticker']}: {yt} -> {new_yt} [{rp.status_code}]")

print(f"\nTotale corretti: {fixed}")
