import requests, re
r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
H={"apikey":anon,"Authorization":"Bearer "+anon}
r2=requests.get("https://mlqkisnizgyvvqajdvbh.supabase.co/rest/v1/stocks",headers=H,
    params={"select":"ticker","in_universe":"eq.true","limit":"3"})
print("  con chiave pubblica -> HTTP",r2.status_code,"righe:",len(r2.json()) if isinstance(r2.json(),list) else r2.json())
