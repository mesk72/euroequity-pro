import os, requests, datetime

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def get_prices(ticker, exchange, limit=800):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                 "order":"date.desc","limit":str(limit)})
    return r.json()

def find_ref_date(prices_desc, target_date):
    # prices_desc: lista ordinata data decrescente [{date, adj_close}, ...]
    # Cerca il primo giorno di trading >= target_date, scorrendo dal piu' vecchio al piu' recente
    # tra quelli disponibili (prices_desc e' decrescente, quindi scorriamo al contrario)
    candidates = [p for p in prices_desc if p["date"] >= target_date.isoformat()]
    if not candidates:
        return None
    # il piu' vecchio tra quelli >= target (cioe' il primo disponibile dopo/uguale al target)
    return min(candidates, key=lambda p: p["date"])

def analyze(ticker, exchange, label):
    prices = get_prices(ticker, exchange)
    if len(prices) < 260:
        print(f"{label} ({ticker}.{exchange}): dati insufficienti ({len(prices)} righe)")
        return
    today_str = prices[0]["date"]
    today_price = prices[0]["adj_close"]
    today_date = datetime.date.fromisoformat(today_str)

    print(f"\n=== {label}: {ticker}.{exchange} ===")
    print(f"Oggi (ultimo dato disponibile): {today_str} = {today_price}")

    # 5 giorni: 4 posizioni indietro nell'array (trading days puri)
    if len(prices) > 4:
        p5 = prices[4]
        chg5 = round((today_price/p5["adj_close"]-1)*100, 2)
        print(f"5 giorni -> riferimento: {p5['date']} = {p5['adj_close']} | var = {chg5}%")

    # 1 mese, 6 mesi, 12 mesi: calendario - N + 1 giorno, poi primo trading day disponibile
    for months, name in [(1,"1 mese"), (6,"6 mesi"), (12,"12 mesi")]:
        target = today_date - datetime.timedelta(days=months*30 if months!=1 else 30)
        # approssimazione calendario: usiamo relativedelta se disponibile, altrimenti mesi*30
        try:
            from dateutil.relativedelta import relativedelta
            target = today_date - relativedelta(months=months)
        except ImportError:
            pass
        target_plus1 = target + datetime.timedelta(days=1)
        ref = find_ref_date(prices, target_plus1)
        if ref:
            chg = round((today_price/ref["adj_close"]-1)*100, 2)
            print(f"{name} -> calendario esatto: {target.isoformat()} | +1gg: {target_plus1.isoformat()} | riferimento reale: {ref['date']} = {ref['adj_close']} | var = {chg}%")
        else:
            print(f"{name} -> nessun dato disponibile per target {target_plus1.isoformat()}")

# Un titolo per continente
analyze("NVDA", "US", "NORD AMERICA")
analyze("ASML", "AS", "EUROPA")  # mic_code AS per Amsterdam, verificato ieri notte
analyze("A005930", "KRX", "ASIA PACIFIC")  # Samsung, verificato ieri notte
