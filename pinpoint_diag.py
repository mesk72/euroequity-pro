import os, requests, time, base64
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
LEEWAY_BASE  = "https://api.leeway.tech/api/v1/public"
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def commit(content_str, path):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(content_str.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": f"diag {path}", "content": content_b64}
    if sha: payload["sha"] = sha
    rp = requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)
    return rp.status_code in (200, 201)

def leeway_ticker(ticker, exchange):
    if exchange == "TSX": return ticker.replace(".", "-") + ".TO"
    if exchange == "BR":  return ticker.replace(".", "") + ".BR"
    if exchange == "US":  return ticker.rstrip(".").replace(".", "-") + ".US"
    suf = {"MIL":".MI","XETRA":".XETRA","PA":".PA","LSE":".LSE","SWX":".SW",
           "OM":".ST","OB":".OL","CPSE":".CO"}.get(exchange, "")
    return ticker.rstrip(".") + suf

lines = []
lines.append(f"Test avviato: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
lines.append(f"LEEWAY_KEY presente: {bool(LEEWAY_KEY)} (lunghezza: {len(LEEWAY_KEY)})")

# Campione REALE di titoli attualmente fermi, presi dal database
samples = []
for ex in ["US", "XETRA", "AS"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker,exchange","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"15"})
    d = r.json()
    if isinstance(d, list):
        samples.extend(d)

lines.append(f"\nCampione: {len(samples)} titoli ({[s['exchange'] for s in samples].count('US')} US, resto EU)")
lines.append("\n--- Chiamate dirette a Leeway, una per una ---")

from datetime import datetime, timedelta
TODAY = datetime.utcnow().strftime("%Y-%m-%d")
FROM_D = (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d")

status_counts = {}
for i, s in enumerate(samples):
    t, ex = s["ticker"], s["exchange"]
    lt = leeway_ticker(t, ex)
    url = f"{LEEWAY_BASE}/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={FROM_D}&to={TODAY}"
    t0 = time.time()
    try:
        resp = requests.get(url, timeout=20)
        elapsed = time.time() - t0
        status_counts[resp.status_code] = status_counts.get(resp.status_code, 0) + 1
        body_snippet = resp.text[:150].replace("\n"," ")
        last_date = "?"
        if resp.status_code == 200:
            try:
                data = resp.json()
                if isinstance(data, list) and data:
                    last_date = sorted(row.get("date","") for row in data)[-1]
            except Exception:
                pass
        lines.append(f"{i+1:3d}. {t:8s}.{ex:6s} ({lt:14s}) HTTP {resp.status_code} in {elapsed:.2f}s  ultima_data={last_date}  body={body_snippet}")
    except Exception as e:
        status_counts["EXC"] = status_counts.get("EXC", 0) + 1
        lines.append(f"{i+1:3d}. {t:8s}.{ex:6s} ({lt:14s}) ECCEZIONE: {e}")
    time.sleep(0.5)
    # Committiamo ogni 10 per non perdere il progresso
    if (i+1) % 10 == 0:
        commit("\n".join(lines), "pinpoint_diag_output.txt")

lines.append(f"\n--- Distribuzione HTTP status codes ---")
lines.append(str(status_counts))
commit("\n".join(lines), "pinpoint_diag_output.txt")
print("Fatto, vedi pinpoint_diag_output.txt")
