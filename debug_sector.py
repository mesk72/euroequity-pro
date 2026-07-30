import requests
r = requests.get("https://forwardalpha.pro/_next/static/chunks/app/page-51cf813554b305ca.js?dpl=x", timeout=20)
print("vecchio chunk (dovrebbe dare 404, nuovo build ha nome diverso):", r.status_code)
r2 = requests.get("https://forwardalpha.pro/", timeout=30)
print("homepage HTTP:", r2.status_code)
import re
m = re.search(r'app/page-([a-f0-9]+)\.js', r2.text)
print("nome chunk homepage attuale:", m.group(0) if m else "non trovato")
