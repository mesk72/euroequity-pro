import requests, re
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1)"}
print("=== HOMEPAGE: deve essere indicizzabile ===")
r=requests.get("https://www.forwardalpha.pro/",timeout=60,headers=UA)
m=re.search(r'<meta name="robots" content="([^"]*)"',r.text)
t=re.search(r"<title>(.*?)</title>",r.text,re.S)
d=re.search(r'<meta name="description" content="(.*?)"',r.text,re.S)
print("  meta robots:", m.group(1) if m else "assente (= indicizzabile)")
print("  header:     ", r.headers.get("x-robots-tag","assente (= indicizzabile)"))
print("  titolo:     ", (t.group(1) if t else "-"))
print("  descrizione:", (d.group(1) if d else "-")[:150])
print()
print("=== PAGINE INTERNE: devono avere noindex ===")
for nome,u in [("scheda AAPL","https://www.forwardalpha.pro/stock/AAPL-US"),
               ("/value","https://www.forwardalpha.pro/value"),
               ("/sectors","https://www.forwardalpha.pro/sectors"),
               ("/news","https://www.forwardalpha.pro/news"),
               ("/about","https://www.forwardalpha.pro/about"),
               ("/legal","https://www.forwardalpha.pro/legal")]:
    rr=requests.get(u,timeout=60,headers=UA)
    mm=re.search(r'<meta name="robots" content="([^"]*)"',rr.text)
    print("  %-13s header: %-22s meta: %s" % (nome, rr.headers.get("x-robots-tag","-"), mm.group(1) if mm else "-"))
