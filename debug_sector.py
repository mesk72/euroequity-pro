import os, requests, re, json
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
SK=os.environ.get("SUPABASE_SERVICE_KEY","")
r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
HA={"apikey":anon,"Authorization":"Bearer "+anon}

print("Cosa vede un ANONIMO oggi (quantita' di righe leggibili):")
for t in ["stocks","fundamentals","prices_eod","latest_prices","sector_quintile_partials",
          "top500_universe","watchlist","profiles","daily_log","script_logs"]:
    try:
        rr=requests.get(BASE+"/rest/v1/"+t,headers={**HA,"Prefer":"count=exact"},
            params={"select":"*","limit":"1"},timeout=25)
        cr=rr.headers.get("content-range","")
        n=cr.split("/")[-1] if "/" in cr else "?"
        print("  %-26s HTTP %s   righe accessibili: %s" % (t,rr.status_code,n))
    except Exception as e:
        print("  %-26s errore %s" % (t,str(e)[:35]))
