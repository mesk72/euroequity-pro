import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def cnt(params):
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},params={**params,"select":"ticker","limit":"1"})
    return int(r.headers.get("content-range","0/0").split("/")[-1])
print("US in_universe=true :", cnt({"exchange":"eq.US","in_universe":"eq.true"}))
print("US in_universe=false:", cnt({"exchange":"eq.US","in_universe":"eq.false"}))
print("US totale          :", cnt({"exchange":"eq.US"}))
print()
print("Righe US in prices_eod al 31/07:")
r=requests.get(U+"/rest/v1/prices_eod",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.US","date":"eq.2026-07-31","limit":"1"})
print("  ", r.headers.get("content-range","?").split("/")[-1])
print("Righe US in latest_prices:")
r2=requests.get(U+"/rest/v1/latest_prices",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.US","limit":"1"})
print("  ", r2.headers.get("content-range","?").split("/")[-1])
print()
print("Campione di titoli US ora fuori universo:")
r3=requests.get(U+"/rest/v1/stocks",headers=H,
    params={"select":"ticker,company,in_universe","exchange":"eq.US","in_universe":"eq.false","limit":"15"})
for x in r3.json(): print("  %-8s %s" % (x["ticker"], (x.get("company") or "")[:45]))
