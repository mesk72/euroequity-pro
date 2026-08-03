import re, requests, json
print("=== 1. La chiave pubblica e' estraibile dal sito? ===")
anon=None
r=requests.get("https://forwardalpha.pro/",timeout=30)
m=re.findall(r'app/[a-zA-Z0-9\-\/_\[\]]+\.js[^"\']*', r.text)
chunks=set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text))
for c in list(chunks)[:20]:
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k:
            anon=k.group(); print("  TROVATA nel bundle:", c[:60]); break
    except Exception: pass
if not anon:
    k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', r.text)
    if k: anon=k.group(); print("  TROVATA nell'HTML")
print("  chiave trovata:", "SI" if anon else "no")
if anon:
    import base64
    p=anon.split(".")[1]; p+="="*(-len(p)%4)
    try: print("  ruolo:", json.loads(base64.b64decode(p)).get("role"))
    except Exception: pass

    print()
    print("=== 2. Con quella chiave, cosa si puo' LEGGERE? ===")
    H={"apikey":anon,"Authorization":"Bearer "+anon}
    for t in ["stocks","fundamentals","prices_eod","latest_prices","profiles",
              "watchlist","portfolios","institutional_viewers","script_logs",
              "daily_log","sector_quintile_partials","top500_universe"]:
        try:
            rr=requests.get("https://mlqkisnizgyvvqajdvbh.supabase.co/rest/v1/"+t,
                headers=H,params={"select":"*","limit":"1"},timeout=20)
            n=len(rr.json()) if rr.status_code==200 and isinstance(rr.json(),list) else 0
            flag="<-- LEGGE DATI" if n>0 else ""
            print("  %-26s HTTP %s  %s" % (t,rr.status_code,flag))
        except Exception as e:
            print("  %-26s errore" % t)

    print()
    print("=== 3. Con quella chiave, si puo' SCRIVERE o CANCELLARE? ===")
    for t in ["stocks","prices_eod","latest_prices"]:
        try:
            w=requests.post("https://mlqkisnizgyvvqajdvbh.supabase.co/rest/v1/"+t,
                headers={**H,"Content-Type":"application/json"},
                json=[{"ticker":"ZZTEST","exchange":"ZZ"}],timeout=20)
            print("  INSERT %-16s HTTP %s %s" % (t,w.status_code,"<-- SCRITTURA PERMESSA!" if w.status_code in (200,201,204) else ""))
        except Exception: print("  INSERT %-16s errore" % t)
        try:
            d=requests.delete("https://mlqkisnizgyvvqajdvbh.supabase.co/rest/v1/"+t,
                headers=H,params={"ticker":"eq.ZZTEST_NON_ESISTE"},timeout=20)
            print("  DELETE %-16s HTTP %s %s" % (t,d.status_code,"<-- CANCELLAZIONE PERMESSA!" if d.status_code in (200,204) else ""))
        except Exception: print("  DELETE %-16s errore" % t)
