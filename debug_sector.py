import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

chunk = ['SEK', 'SMR', 'UOS', 'EDV', 'WES', 'WOW', 'EHL', 'AAC', 'ELS', 'ELV', 'LYC', 'AOV', 'QAN', 'HMC', 'CCP', 'EVN', 'FFM', 'JMS', 'KAR', 'LIN']
from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")

all_rows = []
offset_p = 0
page_num = 0
while True:
    page_num += 1
    params = {"select": "ticker,date,adj_close",
              "exchange": "eq.ASX",
              "ticker": "in.(" + ",".join(chunk) + ")",
              "date": "gte." + from_400d,
              "order": "ticker,date.desc",
              "limit": "1000", "offset": str(offset_p)}
    rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r, params=params)
    batch = rp.json()
    if not isinstance(batch, list) or not batch:
        print(f"Pagina {page_num} (offset={offset_p}): STOP - batch={batch if not isinstance(batch,list) else 'vuoto'}")
        break
    tickers_here = sorted(set(r["ticker"] for r in batch))
    print(f"Pagina {page_num} (offset={offset_p}): {len(batch)} righe, ticker: {tickers_here}")
    all_rows.extend(batch)
    offset_p += 1000
    if len(batch) < 1000:
        print("  -> ultima pagina (batch<1000)")
        break
    if page_num > 15:
        print("  -> STOP DI SICUREZZA (troppo pagine)")
        break

all_tickers_found = set(r["ticker"] for r in all_rows)
print(f"\nTotale righe raccolte: {len(all_rows)}")
print(f"Ticker trovati in totale: {sorted(all_tickers_found)}")
print(f"Ticker MAI trovati: {sorted(set(chunk) - all_tickers_found)}")
