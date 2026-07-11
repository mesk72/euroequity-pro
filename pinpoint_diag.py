import os, requests, time, base64
from datetime import datetime, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
TODAY        = datetime.now().strftime("%Y-%m-%d")
headers_r  = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}

def commit(content_str, path):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(content_str.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": f"update {path}", "content": content_b64}
    if sha: payload["sha"] = sha
    rp = requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)
    return rp.status_code in (200, 201)

out = []
for ticker, exchange in [("JPM","US"), ("AAPL","US")]:
    out.append(f"\n=== {ticker}.{exchange} ===")
    rp = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"})
    d = rp.json()
    last = d[0]["date"] if d else "NESSUNA"
    out.append(f"Ultima data nel DB (prima del test): {last}")

    lt = ticker.rstrip(".").replace(".", "-") + ".US"
    WEEK_AGO = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={WEEK_AGO}&to={TODAY}"
    resp = requests.get(url, timeout=20)
    out.append(f"Leeway ticker: {lt} | HTTP {resp.status_code}")
    data_l = resp.json() if resp.status_code == 200 else []
    if isinstance(data_l, list) and data_l:
        new_max_date = max(row["date"] for row in data_l)
        out.append(f"Leeway restituisce {len(data_l)} righe, ultima_data={new_max_date}")

        price_buf = []
        for row2 in data_l:
            adj = row2.get("adjusted_close") or row2.get("close")
            if adj is None: continue
            price_buf.append({"ticker": ticker, "exchange": exchange,
                               "date": row2["date"], "adj_close": float(adj)})
        out.append(f"Righe pronte per la scrittura: {len(price_buf)}")
        out.append(f"Esempio riga: {price_buf[-1] if price_buf else None}")

        write_resp = requests.post(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_up, json=price_buf, timeout=30)
        out.append(f"Scrittura: HTTP {write_resp.status_code}")
        out.append(f"Corpo risposta scrittura: {write_resp.text[:500]}")

        time.sleep(1)
        rp2 = requests.get(SUPABASE_URL + "/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{ticker}","exchange":f"eq.{exchange}","order":"date.desc","limit":"1"})
        d2 = rp2.json()
        out.append(f"Ultima data nel DB (DOPO il test): {d2[0]['date'] if d2 else 'NESSUNA'}")
    else:
        out.append(f"Leeway non ha restituito dati utilizzabili. Corpo: {resp.text[:300]}")

result = "\n".join(out)
print(result)
commit(result, "surgical_test_output.txt")
