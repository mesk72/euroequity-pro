import requests, json
API_KEY = "aqnMKviDUDoqhp6D9pGuYQWUXYyUZefk"
r = requests.get(f"https://financialmodelingprep.com/stable/income-statement?symbol=2222.SR&apikey={API_KEY}&limit=2", timeout=15)
print(f"HTTP {r.status_code}")
print(r.text[:1500])
