import requests, re
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
r=requests.get("https://forwardalpha.pro/stock/AAPL-US",timeout=60,headers=UA)
h=r.text
# quanto testo VERO vede Google (tolti script e tag)
solo_testo=re.sub(r'<script.*?</script>','',h,flags=re.S)
solo_testo=re.sub(r'<style.*?</style>','',solo_testo,flags=re.S)
solo_testo=re.sub(r'<[^>]+>',' ',solo_testo)
solo_testo=re.sub(r'\s+',' ',solo_testo).strip()
print("HTML totale: %d byte" % len(h))
print("TESTO visibile a Google: %d caratteri" % len(solo_testo))
print()
print("--- cosa legge Google (primi 700 caratteri) ---")
print(solo_testo[:700])
print()
print("--- contiene i dati che rendono la pagina utile? ---")
for k in ["Value Score","Growth Score","P/E","Capitalizzazione","dividend","settore","Information Technology"]:
    print("   %-22s %s" % (k, "SI" if k.lower() in h.lower() else "no"))
print()
print("--- intestazioni H1/H2 (contano molto per Google) ---")
for m in re.findall(r'<h[12][^>]*>(.*?)</h[12]>',h,re.S)[:6]:
    print("   ",re.sub(r'<[^>]+>','',m).strip()[:80])
