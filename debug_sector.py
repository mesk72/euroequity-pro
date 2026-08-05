import requests
print("=== endpoint Vercel -> GitHub ===")
r=requests.get("https://forwardalpha.pro/api/cron/trigger-daily-eu-us",timeout=60)
print("HTTP:", r.status_code)
print(r.text[:350])
