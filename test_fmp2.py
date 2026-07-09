import requests, json
API_KEY = "aqnMKviDUDoqhp6D9pGuYQWUXYyUZefk"
r = requests.get(f"https://financialmodelingprep.com/stable/profile?symbol=2222.SR&apikey={API_KEY}", timeout=15)
data = r.json()
print(json.dumps(data, indent=2))
print()
print("=== Chiavi disponibili ===")
if isinstance(data, list) and data:
    print(list(data[0].keys()))
