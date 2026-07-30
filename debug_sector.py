import requests, re
r = requests.get("https://forwardalpha.pro/", timeout=30)
m = re.search(r'app/page-([a-f0-9]+)\.js', r.text)
print("chunk homepage:", m.group(0) if m else "NON TROVATO")
print("x-vercel-cache:", r.headers.get("x-vercel-cache"), "| age:", r.headers.get("age"))
