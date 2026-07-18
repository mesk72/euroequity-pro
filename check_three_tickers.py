import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"*","ticker":"eq.A005930","exchange":"eq.KRX"})
print("Fundamentals A005930:", r.json())

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.A005930","exchange":"eq.KRX","order":"date.desc","limit":"25"})
prices = r2.json()
print("\nUltimi 25 prezzi:")
for p in prices:
    print(f"  {p}")

if len(prices) >= 22:
    last = prices[0]["adj_close"]
    p1m = prices[21]["adj_close"]
    print(f"\nmom1m ricalcolato ora: {last}/{p1m} - 1 = {round(last/p1m-1,4)}")
