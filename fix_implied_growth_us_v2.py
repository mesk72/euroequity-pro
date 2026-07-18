import os, requests, time
import yfinance as yf

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

RF = 0.0455  # 10Y Treasury, verificato oggi
ERP = 0.05

def implied_growth(price, eps_ntm, ke, gtv=0.025):
    if not price or not eps_ntm or eps_ntm <= 0 or price <= 0 or ke <= gtv:
        return None
    def pv_at_g(g):
        pv = 0.0
        for t in range(1, 11):
            eps_t = eps_ntm * ((1+g)**t)
            pv += eps_t / ((1+ke)**t)
        tv = eps_ntm*((1+g)**10)*(1+gtv) / (ke-gtv)
        pv += tv / ((1+ke)**10)
        return pv
    lo, hi = -0.30, 0.60
    for _ in range(60):
        mid = (lo+hi)/2
        if pv_at_g(mid) > price:
            hi = mid
        else:
            lo = mid
    return round((lo+hi)/2, 6)

universe = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,exchange,eps_ntm_dcf","exchange":"eq.US","eps_ntm_dcf":"not.is.null","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    universe.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

print(f"Titoli US con eps_ntm_dcf: {len(universe)}")

updates = []
errors = 0
processed = 0
for row in universe:
    ticker, exchange, eps_ntm = row["ticker"], row["exchange"], row["eps_ntm_dcf"]
    try:
        r2 = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"})
        p = r2.json()
        if not p:
            continue
        price = p[0]["adj_close"]

        yf_ticker = yf.Ticker(ticker)
        beta = yf_ticker.info.get("beta")
        if beta is None or beta <= 0:
            beta = 1.0  # fallback neutro se Yahoo non ha il dato

        ke = RF + beta * ERP
        ig = implied_growth(price, eps_ntm, ke)
        if ig is not None:
            updates.append({"ticker": ticker, "exchange": exchange, "price": price,
                             "implied_growth": ig, "beta_yf": beta, "ke_used": round(ke,4)})
    except Exception as e:
        errors += 1
        if errors <= 5:
            print(f"  ERRORE {ticker}: {e}")
        continue
    processed += 1
    if processed % 100 == 0:
        print(f"  ...processati {processed}/{len(universe)}, aggiornamenti finora {len(updates)}, errori {errors}")

print(f"Calcolati: {len(updates)} | Errori totali: {errors}")

ok = 0
for i in range(0, len(updates), 100):
    chunk = updates[i:i+100]
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=chunk, timeout=30)
    if resp.status_code in (200,201,204):
        ok += len(chunk)
    else:
        print(f"  WARN: HTTP {resp.status_code} {resp.text[:150]}")

print(f"TOTALE scritti: {ok}/{len(updates)}")
