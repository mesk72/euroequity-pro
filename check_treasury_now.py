import requests, re
from datetime import datetime
year = datetime.now().year
url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
r = requests.get(url, timeout=20)
dates_rates = re.findall(r'<d:NEW_DATE[^>]*>([^<]+)</d:NEW_DATE>.*?<d:BC_10YEAR[^>]*>([^<]+)</d:BC_10YEAR>', r.text, re.DOTALL)
print(f"HTTP {r.status_code}, {len(dates_rates)} righe trovate")
for date, rate in dates_rates[-5:]:
    print(f"  {date[:10]}: {rate}%")
