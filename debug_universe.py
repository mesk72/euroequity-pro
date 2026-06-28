import os, requests, csv, io, math

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

EX_MAP = {
    "XTRA":"XETRA","BIT":"MIL","ENXTPA":"PA","ENXTAM":"AS",
    "ENXTBR":"BR","ENXTLS":"LS","BME":"MC","HLSE":"HE",
    "WBAG":"VI","ISE":"IR","SWX":"SWX","LSE":"LSE","CPSE":"CPSE",
    "NasdaqGS":"US","NYSE":"US","NasdaqCM":"US","AMEX":"US",
    "NasdaqGM":"US","BATS":"US","NYSEArca":"US","OTC":"US",
    "TSX":"TSX","TSXV":"TSX","OB":"OB","OTCNO":"OB",
    "HMSE":"OM","XSAT":"OM",
}

def parse_mktcap(v):
    if not v: return None
    s = str(v).replace("USDMM","").replace("MM","").strip()
    s = s.replace(".","").replace(",",".")
    try:
        f = float(s)
        return f if f > 0 and not math.isnan(f) else None
    except: return None

# Test 1: leggi 5 righe TIKR EU e verifica parsing
print("=== TEST PARSING TIKR EU ===")
r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",
    headers=headers_r)
print(f"Storage status: {r.status_code}")
reader = csv.DictReader(io.StringIO(r.text))
count = 0
for row in reader:
    ticker = row.get("Ticker","").strip()
    ex_raw = row.get("Primary Exchange","").strip()
    exchange = EX_MAP.get(ex_raw, ex_raw)
    mktcap = parse_mktcap(row.get("Last Mkt Cap",""))
    print(f"  {ticker} | ex_raw={ex_raw} | exchange={exchange} | mktcap={mktcap}")
    count += 1
    if count >= 5: break

# Test 2: patch mkt_cap su fundamentals per ASML
print("\n=== TEST PATCH FUNDAMENTALS MKT_CAP ===")
r2 = requests.patch(f"{SUPABASE_URL}/rest/v1/fundamentals",
    headers=headers_up,
    params={"ticker":"eq.ASML","exchange":"eq.AS"},
    json={"mkt_cap": 691603.06})
print(f"ASML patch: {r2.status_code} {r2.text[:100]}")

# Test 3: leggi stocks per AS — verifica company e sector
print("\n=== TEST LETTURA STOCKS AS ===")
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,company,sector",
            "exchange":"eq.AS","limit":"3"})
print(f"Status: {r3.status_code}")
for s in r3.json():
    print(f"  {s['ticker']} | company={s.get('company','')} | sector={s.get('sector','')}")
