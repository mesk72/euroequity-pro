import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")

for query in ["Vodafone", "Unicredit"]:
    r = requests.get("https://api.twelvedata.com/symbol_search", params={"symbol":query,"apikey":API_KEY})
    print(f"\n=== symbol_search: {query} ===")
    d = r.json()
    for item in d.get("data", [])[:8]:
        print(f"  symbol={item.get('symbol')} exchange={item.get('exchange')} mic={item.get('mic_code')} currency={item.get('currency')} country={item.get('country')}")
