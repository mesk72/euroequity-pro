import requests, re
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
print("=== come si comportano gli indirizzi delle schede titolo ===")
prove=[
 ("normale","https://forwardalpha.pro/stock/AAPL-US"),
 ("con barra finale","https://forwardalpha.pro/stock/AAPL-US/"),
 ("minuscolo","https://forwardalpha.pro/stock/aapl-us"),
 ("ticker con spazio","https://forwardalpha.pro/stock/MAERSK B-CPSE"),
 ("spazio codificato","https://forwardalpha.pro/stock/MAERSK%20B-CPSE"),
 ("ticker con punto","https://forwardalpha.pro/stock/IIP.UN-TSX"),
 ("europeo","https://forwardalpha.pro/stock/ASML-AS"),
 ("giapponese","https://forwardalpha.pro/stock/7203-TSE"),
 ("coreano","https://forwardalpha.pro/stock/A005930-KRX"),
]
for nome,u in prove:
    try:
        r=requests.get(u,timeout=45,headers=UA,allow_redirects=False)
        loc=r.headers.get("location","")
        print("  %-20s HTTP %s %s" % (nome,r.status_code,("-> "+loc[:60]) if loc else ""))
    except Exception as e:
        print("  %-20s errore %s" % (nome,str(e)[:40]))
print()
print("=== quali indirizzi mette la sitemap per i ticker particolari? ===")
s=requests.get("https://forwardalpha.pro/sitemap.xml",timeout=90).text
locs=re.findall(r"<loc>(.*?)</loc>", s)
strani=[l for l in locs if "%20" in l or " " in l or "." in l.split("/stock/")[-1] if "/stock/" in l]
print("  indirizzi con spazi o punti: %d" % len(strani))
for l in strani[:10]: print("   ",l)
print()
print("  totale indirizzi in sitemap:", len(locs))
