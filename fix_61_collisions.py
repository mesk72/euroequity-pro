import os, requests, csv, io, re

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

def parse_num(s):
    if not s or s == '-': return None
    s = s.strip()
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()')
    s = s.replace('$','').replace(',','').replace('MM','').replace('x','').strip()
    try:
        v = float(s)
        return -v if neg else v
    except Exception:
        return None

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/tikr_na_latest.csv", headers=headers_r)
text = r.content.decode('utf-8', errors='replace')
reader = csv.DictReader(io.StringIO(text))

by_ticker = {}
for row in reader:
    t = row.get('Ticker','').strip().upper()
    if not t: continue
    by_ticker.setdefault(t, []).append(row)

collisions = {t: rows for t, rows in by_ticker.items() if len(rows) > 1}
print(f"Titoli da correggere: {len(collisions)}")

updates = []
for t, rows in collisions.items():
    usa_row = next((r for r in rows if r.get('Country','').strip().upper() == 'USA'), None)
    if not usa_row:
        print(f"  {t}: nessuna riga USA trovata, salto")
        continue
    mkt_cap = parse_num(usa_row.get('Last Mkt Cap'))
    pb      = parse_num(usa_row.get('LTM P/BVPS LTM'))
    pe_t    = parse_num(usa_row.get('LTM P/E LTM'))
    pe_f    = parse_num(usa_row.get('Mean Fwd P/E NTM'))
    updates.append({"ticker": t, "exchange": "US", "mkt_cap": mkt_cap, "pb": pb,
                     "pe_trailing": pe_t, "pe_forward": pe_f})

print(f"Update pronti: {len(updates)}")
ok = fail = 0
for u in updates:
    resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
        headers=headers_up, json=[u], timeout=20)
    if resp.status_code in (200,201,204):
        ok += 1
    else:
        fail += 1
        print(f"  FALLITO {u['ticker']}: HTTP {resp.status_code} {resp.text[:150]}")

print(f"\nFINALE: ok={ok} fail={fail}")
