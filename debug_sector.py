import requests, re
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
HA={"apikey":anon,"Authorization":"Bearer "+anon}
# storico di un titolo qualsiasi: e' la parte di valore
r=requests.get(BASE+"/rest/v1/prices_eod",headers=HA,
    params={"select":"date,adj_close","ticker":"eq.AAPL","exchange":"eq.US",
            "order":"date.desc","limit":"5"},timeout=30)
print("storico AAPL leggibile da anonimo -> HTTP", r.status_code)
print(r.text[:250])
