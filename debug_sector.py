import requests
print("=== endpoint EU+US ===")
r=requests.get("https://forwardalpha.pro/api/cron/trigger-daily-eu-us",timeout=60)
print("HTTP:",r.status_code); print(r.text[:350])
print()
print("=== endpoint APAC ===")
r2=requests.get("https://forwardalpha.pro/api/cron/trigger-daily-apac",timeout=60)
print("HTTP:",r2.status_code); print(r2.text[:350])
