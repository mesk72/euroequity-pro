import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

EU_EXCHANGES = ['MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS']

all_data = []
for ex in EU_EXCHANGES:
    universe = set()
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        universe.update(s["ticker"] for s in batch)
        offset += 1000
        if len(batch) < 1000: break

    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,value_score,growth_score","exchange":f"eq.{ex}","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for d in batch:
            if d["ticker"] in universe and d.get("value_score") is not None and d.get("growth_score") is not None:
                all_data.append(d["value_score"] + d["growth_score"])
        offset += 1000
        if len(batch) < 1000: break

print(f"Titoli EU con value+growth score: {len(all_data)}")

def pct_rank(arr, val):
    below = sum(1 for x in arr if x < val)
    return round(below / len(arr) * 100)

new_sum = 76 + 80
best_score = min(99, pct_rank(all_data, new_sum))
print(f"\nValue=76 + Growth=80 = {new_sum}")
print(f"Best Score risultante: {best_score}")
