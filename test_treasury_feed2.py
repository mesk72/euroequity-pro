import requests
url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026"
r = requests.get(url, timeout=20)
# Stampa un pezzo vicino alla fine, dove ci sono le entry piu' recenti
text = r.text
print(text[-3000:])
