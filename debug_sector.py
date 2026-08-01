import requests, json
r=requests.get("https://forwardalpha.pro/api/news-cache?region=americas&limit=10",timeout=60)
print("HTTP:", r.status_code)
print("headers rilevanti:", {k:v for k,v in r.headers.items() if k.lower() in ("content-type","cache-control","age","x-vercel-cache","x-matched-path")})
print("corpo (primi 500):", r.text[:500])
