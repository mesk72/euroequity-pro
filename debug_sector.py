import requests, re
r = requests.get("https://forwardalpha.pro/", timeout=30)
print("HTTP homepage:", r.status_code)
m = re.search(r'app/page-([a-f0-9]+)\.js', r.text)
print("chunk homepage:", m.group(0) if m else "NON TROVATO - possibile problema")
# controlla anche l'endpoint API risponda
r2 = requests.get("https://forwardalpha.pro/api/db/stocks?exchanges=US", timeout=30)
print("API stocks HTTP:", r2.status_code)
