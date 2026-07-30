import requests, re
r = requests.get("https://forwardalpha.pro/", timeout=30, headers={"Cache-Control": "no-cache"})
print("HTTP:", r.status_code, "| lunghezza HTML:", len(r.text))
print("x-vercel-cache:", r.headers.get("x-vercel-cache"), "| age:", r.headers.get("age"))

# pattern piu' ampio per qualsiasi riferimento a file .js
js_paths = set(re.findall(r'["\'](/_next/[^"\']+?\.js)["\']', r.text))
print(f"Chunk JS trovati: {len(js_paths)}")

found_old = False
checked = 0
for path in list(js_paths)[:25]:
    full = "https://forwardalpha.pro" + path
    try:
        rj = requests.get(full, timeout=20)
        checked += 1
        if "stockBackTo" in rj.text:
            found_old = True
            print(f"  CODICE VECCHIO ('stockBackTo') trovato in {path}")
    except Exception:
        pass
print(f"Controllati {checked} chunk. Codice vecchio trovato: {found_old}")

# forza bypass cache con query string
r2 = requests.get("https://forwardalpha.pro/?_cachebust=123456", timeout=30)
print("\nCon cachebust - x-vercel-cache:", r2.headers.get("x-vercel-cache"), "| age:", r2.headers.get("age"))
