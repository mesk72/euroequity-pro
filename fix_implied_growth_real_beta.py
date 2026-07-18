import os, requests, subprocess
subprocess.run(["pip", "install", "yfinance", "--break-system-packages", "-q"])
import yfinance as yf

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

RF = 0.0455   # Treasury 10Y, verificato 17 luglio 2026
ERP = 0.05    # premio per il rischio azionario, standard ForwardAlpha
GTV = 0.025   # crescita terminale

def implied_growth(price, eps_ntm, ke):
    if not price or not eps_ntm or eps_ntm <= 0 or price <= 0 or ke <= GTV:
        return None
    def pv_at_g(g):
        pv = 0.0
        for t in range(1, 11):
            eps_t = eps_ntm * ((1+g)**t)
            pv += eps_t / ((1+ke)**t)
        tv = eps_ntm*((1+g)**10)*(1+GTV) / (ke-GTV)
        pv += tv / ((1+ke)**10)
        return pv
    lo, hi = -0.30, 0.60
    for _ in range(50):
        mid = (lo+hi)/2
        if pv_at_g(mid) > price:
            hi = mid
        else:
            lo = mid
    return round((lo+hi)/2, 6)

# Universo US con eps_ntm_dcf e yahoo_ticker
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

print(f"Titoli US con eps_ntm_dcf: {len(universe)}", flush=True)

# Recupera yahoo_ticker per ciascuno
yt_map = {}
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,yahoo_ticker","exchange":"eq.US","limit":"1000"})
offset = 0
while True:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,yahoo_ticker","exchange":"eq.US","limit":"1000","offset":str(offset)})
    batch = r2.json()
    if not isinstance(batch,list) or not batch: break
    for row in batch:
        yt_map[row["ticker"]] = row.get("yahoo_ticker") or row["ticker"]
    offset += 1000
    if len(batch) < 1000: break

updates = []
errors = 0
no_beta = 0
processed = 0

for row in universe:
    ticker, exchange, eps_ntm = row["ticker"], row["exchange"], row["eps_ntm_dcf"]
    yticker = yt_map.get(ticker, ticker)

    try:
        # Prezzo fresco da prices_eod
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"adj_close","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"}, timeout=15)
        pdata = rp.json()
        if not pdata:
            processed += 1
            continue
        price = pdata[0]["adj_close"]

        # Beta reale da Yahoo
        t = yf.Ticker(yticker)
        beta = t.info.get("beta")
        if beta is None:
            no_beta += 1
            processed += 1
            continue

        ke = RF + beta * ERP
        ig = implied_growth(price, eps_ntm, ke)
        if ig is not None:
            updates.append({"ticker": ticker, "exchange": exchange, "price": price,
                             "beta": round(beta,4), "ke": round(ke,6), "implied_growth_10y": ig})
    except Exception as e:
        errors += 1

    processed += 1
    if processed % 100 == 0:
        print(f"  {processed}/{len(universe)} | calcolati {len(updates)} | no_beta {no_beta} | errori {errors}", flush=True)

    if len(updates) >= 300:
        ok = 0
        for i in range(0, len(updates), 150):
            chunk = updates[i:i+150]
            resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
                headers=headers_up, json=chunk, timeout=30)
            if resp.status_code in (200,201,204): ok += len(chunk)
        print(f"  Scrittura parziale: {ok}/{len(updates)}", flush=True)
        updates = []

if updates:
    ok = 0
    for i in range(0, len(updates), 150):
        chunk = updates[i:i+150]
        resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
            headers=headers_up, json=chunk, timeout=30)
        if resp.status_code in (200,201,204): ok += len(chunk)
    print(f"  Scrittura finale: {ok}/{len(updates)}", flush=True)

print(f"COMPLETATO. Processati {processed}, no_beta {no_beta}, errori {errors}", flush=True)
