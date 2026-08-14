import requests, re
r=requests.get("https://forwardalpha.pro/stock/SBUX-US",timeout=60)
h=r.text
print("=== Link a Yahoo nella pagina Starbucks in produzione ===")
for l in sorted(set(re.findall(r'https://finance\.yahoo\.com/quote/[^"\'<> ]+', h))):
    print("  ",l)
print()
print("Il link Estimates forza l'inglese:", any("analysis" in l and "hl=en-US" in l for l in re.findall(r'https://finance\.yahoo\.com/quote/[^"\'<> ]+', h)))
