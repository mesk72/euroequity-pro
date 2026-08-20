import requests, re
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
for nome,u in [("/value","https://forwardalpha.pro/value"),
               ("/dividends","https://forwardalpha.pro/dividends"),
               ("/sectors","https://forwardalpha.pro/sectors"),
               ("/research","https://forwardalpha.pro/research"),
               ("/about","https://forwardalpha.pro/about"),
               ("home","https://forwardalpha.pro/")]:
    try:
        r=requests.get(u,timeout=60,headers=UA)
        h=r.text
        t=re.sub(r'<script.*?</script>','',h,flags=re.S)
        t=re.sub(r'<style.*?</style>','',t,flags=re.S)
        t=re.sub(r'<[^>]+>',' ',t); t=re.sub(r'\s+',' ',t).strip()
        ti=re.search(r"<title>(.*?)</title>",h,re.S)
        h1=re.findall(r'<h1[^>]*>(.*?)</h1>',h,re.S)
        print("%-12s HTTP %s | testo %5d car | H1: %s" % (nome,r.status_code,len(t),
              (re.sub(r'<[^>]+>','',h1[0]).strip()[:45] if h1 else "ASSENTE")))
        print("             titolo: %s" % ((ti.group(1) if ti else "-")[:75]))
    except Exception as e:
        print("%-12s errore %s" % (nome,str(e)[:40]))
