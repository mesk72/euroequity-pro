import requests
r = requests.get("https://forwardalpha.pro/?page=globalscreen&scr_ex=KRX", timeout=30)
print("HTTP:", r.status_code, "| lunghezza:", len(r.text))
print("Contiene errore visibile:", "Application error" in r.text or "500" in r.text[:200])
