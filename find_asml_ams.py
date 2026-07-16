import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")

r = requests.get("https://api.twelvedata.com/statistics", params={"symbol":"ASML","mic_code":"XAMS","apikey":API_KEY})
d = r.json()
print("Status:", r.status_code)
if "meta" in d:
    print("Currency:", d["meta"].get("currency"), "| Exchange:", d["meta"].get("exchange"))
    fin = d.get("statistics",{}).get("financials",{})
    print("EPS TTM:", fin.get("income_statement",{}).get("diluted_eps_ttm"))
    print("Revenue TTM:", fin.get("income_statement",{}).get("revenue_ttm"))
    print("BVPS:", fin.get("balance_sheet",{}).get("book_value_per_share_mrq"))
    print("Fiscal year end:", fin.get("fiscal_year_ends"))
print(json.dumps(d)[:800])

# earnings_estimate e revenue_estimate stesso simbolo/mic
for ep in ["earnings_estimate","revenue_estimate"]:
    r2 = requests.get(f"https://api.twelvedata.com/{ep}", params={"symbol":"ASML","mic_code":"XAMS","period":"annual","apikey":API_KEY})
    print(f"\n=== {ep} ===")
    print(json.dumps(r2.json(), indent=1)[:1200])
