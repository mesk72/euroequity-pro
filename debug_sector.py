import requests, re
r=requests.get("https://forwardalpha.pro/",timeout=40)
chunks=set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text))
# cerca anche i chunk della pagina titolo
r2=requests.get("https://forwardalpha.pro/stock/SBUX-US",timeout=60)
chunks |= set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r2.text))
trovati=[]
for c in chunks:
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=25).text
        if "/analysis" in j:
            for m in re.findall(r'finance\.yahoo\.com/quote/[^"\`\']{0,120}analysis[^"\`\']{0,80}', j):
                trovati.append(m)
    except Exception: pass
print("Link 'analysis' trovati nel codice pubblicato:")
for t in sorted(set(trovati)): print("  ",t)
print()
print("Contengono hl=en-US:", all("hl=en-US" in t for t in trovati) if trovati else "nessun link trovato")
