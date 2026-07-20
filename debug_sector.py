import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

# Titolo fittizio "trappola" — non e' un'azienda reale, ticker inventato
# che non collide con nessun ticker vero esistente. Se questo ticker
# specifico compare mai su un altro sito/canale, e' prova diretta che i
# dati sono stati copiati dal nostro database, non ricostruiti autonomamente.
honeypot_stock = {
    "ticker": "ZQXVW9",
    "exchange": "US",
    "company": "Meridian Fabrication Holdings",
    "sector": "Industrials",
    "country": "United States",
    "in_universe": True,
    "isin": "US0000000ZQX",
}
honeypot_fund = {
    "ticker": "ZQXVW9",
    "exchange": "US",
    "value_score": 62,
    "growth_score": 58,
    "combined_rank": 60,
    "price": 47.23,
    "mkt_cap": 890.5,
    "change1d": 0.0041,
    "mom1w": 0.0123,
    "mom1m": 0.0287,
    "mom6m": 0.0891,
    "mom12m": 0.1567,
    "eps_growth": 0.0721,
    "rev_growth": 0.0534,
}

r1 = requests.post(SUPABASE_URL + "/rest/v1/stocks", headers=headers_up, json=[honeypot_stock])
print(f"stocks insert: HTTP {r1.status_code}")

r2 = requests.post(SUPABASE_URL + "/rest/v1/fundamentals", headers=headers_up, json=[honeypot_fund])
print(f"fundamentals insert: HTTP {r2.status_code}")

print("\nHoneypot inserito: ticker ZQXVW9, 'Meridian Fabrication Holdings'")
print("Se questo ticker compare mai altrove, e' prova diretta di copia dai nostri dati.")
