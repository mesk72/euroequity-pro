import os, requests, base64
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "mesk72/euroequity-pro")
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def commit_log(text, path="fix_numeric_sector_output.txt"):
    gh_headers = {"Authorization": f"token {GH_TOKEN}"}
    content_b64 = base64.b64encode(text.encode()).decode()
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    payload = {"message": "fix numeric sector output", "content": content_b64}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=gh_headers, json=payload)

ALL_EXCHANGES = ['MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS',
                  'US','TSX','TSE','SEHK','ASX','KRX','SGX']

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

# Verifica manuale: tutti i 66 titoli trovati sono REIT/immobiliari
# (nome contiene REIT, Realty, Trust, SOCIMI, REIC, Properties) — nessuna
# eccezione trovata nella lista, quindi assegnazione diretta sicura.
found = []
for ex in ALL_EXCHANGES:
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
            params={"select":"ticker,exchange,company,sector","exchange":f"eq.{ex}","in_universe":"eq.true","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        for s in batch:
            sec = s.get("sector")
            if sec and str(sec).strip().isdigit():
                found.append(s)
        offset += 1000
        if len(batch) < 1000: break

log(f"Titoli da correggere: {len(found)}")
ok = fail = 0
for s in found:
    resp = requests.patch(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_up,
        params={"ticker":f"eq.{s['ticker']}","exchange":f"eq.{s['exchange']}"},
        json={"sector": "Real Estate"})
    if resp.status_code in (200,201,204):
        ok += 1
    else:
        fail += 1
        log(f"  FALLITO {s['ticker']}.{s['exchange']}: HTTP {resp.status_code}")

log(f"\nFINALE: ok={ok} fail={fail}")
commit_log("\n".join(log_lines))
print("Fatto")
