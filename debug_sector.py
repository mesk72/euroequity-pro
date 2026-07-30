import requests
r = requests.get("https://forwardalpha.pro/", timeout=30)
print("Homepage HTTP:", r.status_code)
# cerca link a chunk JS
import re
js_links = re.findall(r'src="(/_next/static/[^"]+\.js)"', r.text)
print(f"Trovati {len(js_links)} chunk JS")
found_old_string = False
for link in js_links[:15]:
    full = "https://forwardalpha.pro" + link
    try:
        rj = requests.get(full, timeout=20)
        if "stockBackTo" in rj.text:
            print(f"TROVATO 'stockBackTo' (CODICE VECCHIO) in: {link}")
            found_old_string = True
    except Exception as e:
        print(f"errore su {link}: {e}")
if not found_old_string:
    print("Stringa 'stockBackTo' (codice vecchio) NON trovata nei chunk controllati")

# Controlla header deployment
print("\nHeader risposta homepage:")
for h in ["x-vercel-id", "age", "x-vercel-cache", "date"]:
    print(f"  {h}: {r.headers.get(h)}")
