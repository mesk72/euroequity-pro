import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,price,change1d","ticker":"eq.9984","exchange":"eq.TSE"})
print("Valore attuale in fundamentals:", r.json())

# Calcolo reale dal prezzo storico
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.9984","exchange":"eq.TSE","order":"date.desc","limit":"5"})
prices = r2.json()
print("\nUltimi prezzi:")
for p in prices:
    print(" ", p)
if len(prices) >= 2:
    real_change = prices[0]["adj_close"] / prices[1]["adj_close"] - 1
    print(f"\nVariazione reale calcolata ({prices[1]['date']} -> {prices[0]['date']}): {real_change*100:.2f}%")
