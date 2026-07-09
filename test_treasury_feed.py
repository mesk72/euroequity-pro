import requests, re

url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026"
r = requests.get(url, timeout=20)
print(f"HTTP {r.status_code}, {len(r.text)} bytes")
# trova le ultime voci (l'XML e' ordinato, ultime righe = piu' recenti di solito)
matches = re.findall(r'<d:NEW_DATE>([^<]+)</d:NEW_DATE>.*?<d:BC_10YEAR>([^<]+)</d:BC_10YEAR>', r.text, re.DOTALL)
print(f"Trovate {len(matches)} righe con data+10Y")
for date, rate in matches[-5:]:
    print(f"  {date}: {rate}%")
