import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,change1d,price","ticker":"eq.NVDA","exchange":"eq.US"})
print("NVDA fundamentals ora:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.NVDA","exchange":"eq.US","order":"date.desc","limit":"3"})
prices = r2.json()
print("Ultimi 3 prezzi:", prices)
if len(prices) >= 2:
    check = round((prices[0]["adj_close"]/prices[1]["adj_close"]-1)*100, 4)
    print(f"Verifica manuale change1d: {check}%")
