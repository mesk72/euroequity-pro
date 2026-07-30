import requests
r = requests.get("https://forwardalpha.pro/", timeout=30)
print("serviceWorker" in r.text, "| menzioni 'serviceWorker' nell'HTML iniziale")
r2 = requests.get("https://forwardalpha.pro/sw.js", timeout=15)
print("sw.js:", r2.status_code)
r3 = requests.get("https://forwardalpha.pro/service-worker.js", timeout=15)
print("service-worker.js:", r3.status_code)
r4 = requests.get("https://forwardalpha.pro/manifest.json", timeout=15)
print("manifest.json:", r4.status_code, r4.text[:300] if r4.status_code==200 else "")
