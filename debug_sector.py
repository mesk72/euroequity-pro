import requests
try:
    r = requests.get("https://forwardalpha.pro/api/cron/trigger-daily-apac", timeout=30)
    print("Status:", r.status_code)
    print("Body:", r.text[:500])
except Exception as e:
    print("ERRORE chiamata:", e)
