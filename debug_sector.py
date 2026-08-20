import requests, re
UA={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
r=requests.get("https://forwardalpha.pro/",timeout=60,headers=UA)
h=r.text
t=re.sub(r'<script.*?</script>','',h,flags=re.S)
t=re.sub(r'<style.*?</style>','',t,flags=re.S)
t=re.sub(r'<[^>]+>',' ',t); t=re.sub(r'\s+',' ',t).strip()
print("HOMEPAGE — testo visibile a Google: %d caratteri (prima: 60)" % len(t))
print()
h1=re.findall(r'<h1[^>]*>(.*?)</h1>',h,re.S)
print("H1:", re.sub(r'<[^>]+>','',h1[0]).strip()[:90] if h1 else "ASSENTE")
print("H2 presenti:", len(re.findall(r'<h2[^>]*>',h)))
for m in re.findall(r'<h2[^>]*>(.*?)</h2>',h,re.S)[:8]:
    print("   -",re.sub(r'<[^>]+>','',m).strip()[:60])
print()
print("--- primi 400 caratteri che legge Google ---")
print(t[:400])
print()
print("--- controllo protezione punteggi ---")
import re as r2
num=r2.findall(r'[Vv]alue [Ss]core[^0-9]{0,20}(\d+)',h)
print("  valori numerici di Value Score nell'HTML:", num if num else "NESSUNO")
print("  la parola 'classifica'/'ranking' con elenchi:", "no" if "top 10" not in h.lower() else "VERIFICARE")
