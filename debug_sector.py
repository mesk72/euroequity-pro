import requests
r = requests.get("https://forwardalpha.pro/api/db/stocks?exchanges=US", timeout=60)
print("API HTTP:", r.status_code)
leftovers = [h for h in r.headers if h.lower().startswith(("x-timing","x-quintile"))]
print("Intestazioni di debug residue:", leftovers if leftovers else "NESSUNA")
p = requests.get("https://forwardalpha.pro/", timeout=30)
print("Sito HTTP:", p.status_code)
