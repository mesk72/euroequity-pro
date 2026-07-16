import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
for sym in ["DE","CTAS","FDS","PAYX","MU"]:
    try:
        r = requests.get("https://api.twelvedata.com/statistics", params={"symbol":sym,"apikey":API_KEY})
        d = r.json()
        fy = d.get("statistics",{}).get("financials",{}).get("fiscal_year_ends")
        print(f"{sym}: fiscal_year_ends = {fy}")
    except Exception as e:
        print(f"{sym}: ERRORE {e}")
