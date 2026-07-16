import os, requests
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
# Cerchiamo titoli con FY end circa 15-25 giorni fa da oggi (16 luglio) -> fine giugno/inizio luglio
for sym in ["JEF","ACN","CTAS","AVGO","LEN","WBA","ADBE","PLCE","AZO"]:
    try:
        r = requests.get("https://api.twelvedata.com/statistics", params={"symbol":sym,"apikey":API_KEY})
        d = r.json()
        fy = d.get("statistics",{}).get("financials",{}).get("fiscal_year_ends")
        print(f"{sym}: fiscal_year_ends = {fy}")
    except Exception as e:
        print(f"{sym}: ERRORE {e}")
