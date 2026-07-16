import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")

# Prova varie sintassi per ASML su Amsterdam
for sym in ["ASML:XAMS", "ASML.AS", "ASML:AMS"]:
    r = requests.get("https://api.twelvedata.com/statistics", params={"symbol":sym,"apikey":API_KEY})
    d = r.json()
    print(f"\n=== {sym} (status {r.status_code}) ===")
    if "meta" in d:
        print("Currency:", d["meta"].get("currency"), "| Exchange:", d["meta"].get("exchange"))
        print("EPS TTM:", d.get("statistics",{}).get("financials",{}).get("income_statement",{}).get("diluted_eps_ttm"))
    else:
        print(json.dumps(d)[:300])

# Symbol search per trovare la sintassi esatta
r2 = requests.get("https://api.twelvedata.com/symbol_search", params={"symbol":"ASML","apikey":API_KEY})
print("\n=== symbol_search ASML ===")
print(json.dumps(r2.json(), indent=1)[:1500])
