import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

chunk = ['SEK', 'SMR', 'UOS', 'EDV', 'WES', 'WOW', 'EHL', 'AAC', 'ELS', 'ELV', 'LYC', 'AOV', 'QAN', 'HMC', 'CCP', 'EVN', 'FFM', 'JMS', 'KAR', 'LIN']
from_400d = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")

all_ph = {}
offset_p = 0
page = 0
while True:
    rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select": "ticker,date,adj_close",
                "exchange": "eq.ASX",
                "ticker": "in.(" + ",".join(chunk) + ")",
                "date": "gte." + from_400d,
                "order": "ticker,date.desc",
                "limit": "1000", "offset": str(offset_p)})
    batch = rp.json()
    page += 1
    if not isinstance(batch, list) or not batch:
        print(f"Pagina {page} (offset={offset_p}): VUOTA o errore -> {str(batch)[:200]}")
        break
    tickers_in_page = sorted(set(b["ticker"] for b in batch))
    print(f"Pagina {page} (offset={offset_p}): {len(batch)} righe, ticker presenti: {tickers_in_page}")
    for b in batch:
        all_ph.setdefault(b["ticker"], []).append(b["date"])
    offset_p += 1000
    if len(batch) < 1000:
        print(f"  -> ultima pagina (batch<1000)")
        break
    if page > 15:
        print("  -> STOP DI SICUREZZA dopo 15 pagine")
        break

print(f"\nTicker totali raccolti: {sorted(all_ph.keys())}")
print(f"Ticker del chunk MANCANTI: {[t for t in chunk if t not in all_ph]}")
print(f"WES presente: {'WES' in all_ph}, righe: {len(all_ph.get('WES',[]))}")
