import requests, re
r = requests.get("https://forwardalpha.pro/", timeout=30)
m = re.search(r'app/page-([a-f0-9]+)\.js', r.text)
print("chunk homepage:", m.group(0) if m else "non trovato")
