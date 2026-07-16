import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}

EU_EXCHANGES = ['MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS']

total_fixed = 0
for ex in EU_EXCHANGES:
    rows = []
    offset = 0
    while True:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
            params={"select":"ticker,exchange,change1d","exchange":f"eq.{ex}","change1d":"not.is.null","limit":"1000","offset":str(offset)})
        batch = r.json()
        if not isinstance(batch,list) or not batch: break
        rows.extend(batch)
        offset += 1000
        if len(batch) < 1000: break

    # Correggi solo i valori che sembrano gia' moltiplicati per 100
    # (soglia di sicurezza: un vero change1d giornaliero raramente supera
    # 0.5 in valore assoluto = 50%, quindi valori oltre 1.0 sono quasi
    # certamente il bug x100)
    updates = []
    for row in rows:
        val = row["change1d"]
        if val is not None and abs(val) > 1.0:
            updates.append({"ticker": row["ticker"], "exchange": row["exchange"], "change1d": round(val / 100, 6)})

    if updates:
        ok = 0
        for i in range(0, len(updates), 200):
            chunk = updates[i:i+200]
            resp = requests.post(SUPABASE_URL + "/rest/v1/fundamentals?on_conflict=ticker,exchange",
                headers=headers_up, json=chunk, timeout=30)
            if resp.status_code in (200,201,204):
                ok += len(chunk)
            else:
                print(f"  WARN {ex}: HTTP {resp.status_code} {resp.text[:150]}")
        print(f"{ex}: {ok}/{len(updates)} corretti (su {len(rows)} totali controllati)")
        total_fixed += ok
    else:
        print(f"{ex}: 0 da correggere (su {len(rows)} totali controllati)")

print(f"\nTOTALE corretti: {total_fixed}")
