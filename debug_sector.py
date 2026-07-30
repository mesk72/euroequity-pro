import requests
url = "https://forwardalpha.pro/_next/static/chunks/app/page-51cf813554b305ca.js?dpl=dpl_FeXinXVV5BUafZdouBC9X6jDVghF"
r = requests.get(url, timeout=30)
print("HTTP:", r.status_code, "| lunghezza:", len(r.text))
print("Contiene 'stockBackTo' (codice VECCHIO):", "stockBackTo" in r.text)
print("Contiene 'stateless' (commento nuovo codice):", "stateless" in r.text.lower())
print("Contiene 'X-Timing' o 'Timing-Total' (nuovo timing):", "Timing" in r.text)
# cerca goToStock nel testo per contesto
idx = r.text.find("stockBackTo")
if idx >= 0:
    print("Contesto attorno a stockBackTo:", r.text[max(0,idx-100):idx+100])
