import os, requests, csv, io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EX_MAP_APAC = {
    "TSE": "TSE", "TYO": "TSE", "XTKS": "TSE",
    "SEHK": "SEHK", "HKG": "SEHK", "XHKG": "SEHK",
    "ASX": "ASX", "XASX": "ASX",
    "KOSE": "KRX", "KOSDAQ": "KRX",
    "SGX": "SGX", "Catalist": "SGX", "NSE": "SGX", "SPSE": "SGX", "NSX": "SGX", "XKON": "SGX",
}

r = requests.get(SUPABASE_URL + "/storage/v1/object/tikr-uploads/tikr_apac_latest.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))

count_krx = 0
count_sgx = 0
for row in reader:
    ex_tikr = row.get("Primary Exchange", "").strip()
    exchange = EX_MAP_APAC.get(ex_tikr, "")
    if exchange == "KRX" and count_krx < 5:
        print(f"KRX ticker={row.get('Ticker')} mktcap={row.get('Market Cap') or row.get('Mkt Cap')} "
              f"pe_fwd={row.get('Mean Forward P/E NTM')} pb={row.get('Trailing P/BVPS LTM')} "
              f"rev_fy0={row.get('Revenue (FY 2025)')} rev_fy1={row.get('Mean Revenue (FY 2026)')}")
        count_krx += 1
    if exchange == "SGX" and count_sgx < 5:
        print(f"SGX ticker={row.get('Ticker')} mktcap={row.get('Market Cap') or row.get('Mkt Cap')} "
              f"pe_fwd={row.get('Mean Forward P/E NTM')} pb={row.get('Trailing P/BVPS LTM')} "
              f"rev_fy0={row.get('Revenue (FY 2025)')} rev_fy1={row.get('Mean Revenue (FY 2026)')}")
        count_sgx += 1
    if count_krx >= 5 and count_sgx >= 5:
        break
