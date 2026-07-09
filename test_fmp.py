import requests, json

API_KEY = "aqnMKviDUDoqhp6D9pGuYQWUXYyUZefk"

# 1. Prova a cercare titoli GCC con l'endpoint di ricerca, per scoprire il formato ticker corretto
print("=" * 60)
print("[1] Search per 'Saudi Aramco' / 'DBS' / aziende note GCC")
print("=" * 60)
for q in ["Saudi Arabian Oil", "Al Rajhi", "Emirates NBD", "Qatar National Bank"]:
    try:
        r = requests.get(f"https://financialmodelingprep.com/stable/search-symbol?query={q}&apikey={API_KEY}", timeout=15)
        print(f"  Query '{q}': HTTP {r.status_code}")
        print(f"    {r.text[:500]}")
    except Exception as e:
        print(f"  Query '{q}': ERRORE {e}")

print()
print("=" * 60)
print("[2] Test diretto profilo su ticker ipotizzati (stile Yahoo)")
print("=" * 60)
test_tickers = ["2222.SR", "1120.SR", "QNBK.QA", "EMIRATESNBD.AE", "KFH.KW"]
for t in test_tickers:
    try:
        r = requests.get(f"https://financialmodelingprep.com/stable/profile?symbol={t}&apikey={API_KEY}", timeout=15)
        print(f"  {t}: HTTP {r.status_code}")
        print(f"    {r.text[:600]}")
    except Exception as e:
        print(f"  {t}: ERRORE {e}")
