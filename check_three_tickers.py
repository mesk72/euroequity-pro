import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Cerca in tutto lo storico prezzi NVDA quali date hanno prezzo vicino a 195
r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.NVDA","exchange":"eq.US","order":"date.desc","limit":"60"})
prices = r.json()
print("Ultimi 60 giorni di prezzo NVDA, cerco vicino a 195:")
for p in prices:
    marker = " <-- VICINO A 195" if 193 <= p["adj_close"] <= 197 else ""
    print(f"  {p['date']}: {p['adj_close']}{marker}")

# Verifica anche se implied_growth=0.17 combacia con quale prezzo esatto
# usando eps_ntm_dcf=10.0084 e vari Ke possibili, per capire il prezzo implicito nel 17%
print("\n--- Verifica inversa: quale prezzo darebbe esattamente 17% con Ke=0.15605 ---")
eps_ntm = 10.0084
ke = 0.15605
gtv = 0.025
def pv_at_g(g):
    pv = 0.0
    for t in range(1, 11):
        pv += eps_ntm * ((1+g)**t) / ((1+ke)**t)
    tv = eps_ntm*((1+g)**10)*(1+gtv) / (ke-gtv)
    pv += tv / ((1+ke)**10)
    return pv
price_at_17pct = pv_at_g(0.17)
print(f"Prezzo che darebbe esattamente il 17% di crescita implicita: {price_at_17pct:.2f}")
