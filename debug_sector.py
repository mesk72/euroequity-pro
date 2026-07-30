import requests
r = requests.get("https://forwardalpha.pro/api/db/history?ticker=AAPL&exchange=US&days=1825", timeout=30)
print("HTTP:", r.status_code)
print("Contenuto completo:", r.text)
print("Headers:", dict(r.headers))
