import requests
r=requests.get("https://forwardalpha.pro/api/cron/trigger-daily-eu",timeout=60)
print("HTTP",r.status_code,r.text[:200])
