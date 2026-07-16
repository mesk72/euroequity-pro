import os, requests, json
API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")

def call(sym, endpoint, params=None):
    p = params or {}
    p["symbol"] = sym
    p["apikey"] = API_KEY
    r = requests.get(f"https://api.twelvedata.com/{endpoint}", params=p)
    print(f"\n=== {sym} / {endpoint} {params or ''} ===")
    print(json.dumps(r.json(), indent=1)[:1800])

# ASML - verifica valuta EPS/Revenue
call("ASML", "statistics")
call("ASML", "earnings")

# Toyota - normalized vs GAAP, valuta
call("TM", "statistics")   # ADR quotato in USD su NYSE
call("7203", "statistics") # possibile ticker Tokyo diretto

# Conferma che ORCL abbia davvero riportato FY26 (non stima)
call("ORCL", "earnings", {"outputsize":"1"})

# Candidato aprile - Casey's General Stores
call("CASY", "statistics")
