import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.NVDA","exchange":"eq.US","order":"date.desc","limit":"25"})
prices = r.json()
print("Ultimi 25 giorni di trading NVDA (indice 0 = piu' recente):")
for i, p in enumerate(prices):
    marker = " <-- PUNTO DI PARTENZA (indice 21, 1 mese = 21 giorni trading)" if i == 21 else ""
    print(f"  [{i}] {p['date']}: {p['adj_close']}{marker}")

if len(prices) >= 22:
    last = prices[0]["adj_close"]
    start = prices[21]["adj_close"]
    print(f"\nPunto di arrivo (oggi): {prices[0]['date']} = {last}")
    print(f"Punto di partenza (21 giorni trading fa): {prices[21]['date']} = {start}")
    print(f"mom1m = {round((last/start-1)*100,2)}%")
