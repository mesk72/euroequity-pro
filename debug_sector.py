import requests, re
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
for nome,u in [("/legal","https://www.forwardalpha.pro/legal"),
               ("/about","https://www.forwardalpha.pro/about")]:
    r=requests.get(u,timeout=60,headers=UA)
    t=re.sub(r'<script.*?</script>','',r.text,flags=re.S)
    t=re.sub(r'<[^>]+>',' ',t); t=re.sub(r'\s+',' ',t).strip()
    print("%-8s HTTP %s | testo %5d car | menzione 'personal use': %s" % (
        nome, r.status_code, len(t), "only for personal use" in r.text))
    print("   inizio:", t[:110])
