import os, requests
from datetime import timedelta
from dateutil.relativedelta import relativedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def get_history(ticker, exchange):
    all_rows = []
    frm = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date,adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}",
                    "order":"date.asc","offset":str(frm),"limit":"1000"})
        d = r.json()
        if not d: break
        all_rows.extend(d)
        if len(d) < 1000: break
        frm += 1000
    return all_rows

for ticker, exchange in [("ASML","AS"), ("MC","PA")]:
    data = get_history(ticker, exchange)
    print(f"\n===== {ticker}.{exchange} — {len(data)} record totali, ultimo: {data[-1]['date']} =====")
    last_date_str = data[-1]["date"]
    last_price = data[-1]["adj_close"]
    from datetime import datetime
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()

    # METODO GRAFICO (fisso indice 127 trading days)
    idx_chart = len(data) - 1 - 127
    chart_ref = data[idx_chart]
    mom6m_chart = (last_price / chart_ref["adj_close"] - 1) * 100

    # METODO SCREENER (data di calendario -6 mesi, poi prende il primo disponibile >= target+1)
    target = last_date - relativedelta(months=6)
    target_plus1 = target + timedelta(days=1)
    candidates = [p for p in data if p["date"] >= target_plus1.isoformat()]
    screener_ref = min(candidates, key=lambda p: p["date"])
    mom6m_screener = (last_price / screener_ref["adj_close"] - 1) * 100

    print(f"Data odierna (ultimo prezzo): {last_date_str}  prezzo={last_price}")
    print(f"--- Metodo GRAFICO (indice fisso 127gg trading) ---")
    print(f"  Data riferimento: {chart_ref['date']}  prezzo={chart_ref['adj_close']}")
    print(f"  mom6m = {mom6m_chart:.2f}%")
    print(f"--- Metodo SCREENER (calendario -6 mesi) ---")
    print(f"  Data target: {target.isoformat()} (6 mesi calendario prima)")
    print(f"  Data riferimento trovata: {screener_ref['date']}  prezzo={screener_ref['adj_close']}")
    print(f"  mom6m = {mom6m_screener:.2f}%")
    print(f"--- SCARTO ---")
    days_diff = (datetime.strptime(chart_ref['date'],'%Y-%m-%d').date() - datetime.strptime(screener_ref['date'],'%Y-%m-%d').date()).days
    print(f"  Differenza date di riferimento: {days_diff} giorni di calendario")
    print(f"  Differenza mom6m: {mom6m_chart - mom6m_screener:.2f} punti percentuali")

    # Conta effettivi giorni di trading tra screener_ref e last_date, per vedere se 127 è corretto
    trading_days_between = sum(1 for p in data if p["date"] > screener_ref["date"] and p["date"] <= last_date_str)
    print(f"  Giorni di trading REALI tra la data corretta (-6 mesi) e oggi: {trading_days_between} (il grafico assume fisso 127)")
