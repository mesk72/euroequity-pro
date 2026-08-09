import requests, re
print("=== Cosa vede GOOGLE aprendo una scheda titolo? ===")
r=requests.get("https://forwardalpha.pro/stock/AAPL-US",timeout=60,
    headers={"User-Agent":"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"})
h=r.text
print("HTTP:",r.status_code,"| lunghezza HTML:",len(h))
t=re.search(r"<title>(.*?)</title>",h,re.S)
print("titolo:", t.group(1)[:110] if t else "ASSENTE")
d=re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',h,re.S)
print("descrizione:", (d.group(1)[:130] if d else "ASSENTE"))
print()
for parola in ["Apple","AAPL","Value Score","Growth","Market Cap","P/E"]:
    print("  contiene '%s': %s" % (parola, parola.lower() in h.lower()))
print()
print("Dati strutturati (schema.org):", "application/ld+json" in h)
