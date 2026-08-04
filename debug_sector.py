import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]
TUTTI=EU+["US","TSX","TSE","SEHK","ASX","KRX","SGX"]

print("=== Quante righe restituisce la query SENZA paginazione? ===")
r=requests.get(U+"/rest/v1/latest_prices",headers=H,
    params={"select":"ticker,exchange,price,price_date,change1d",
            "exchange":"in.("+",".join(TUTTI)+")"})
d=r.json()
print("  righe ottenute:", len(d) if isinstance(d,list) else d)
rc=requests.get(U+"/rest/v1/latest_prices",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"in.("+",".join(TUTTI)+")","limit":"1"})
print("  righe REALMENTE esistenti:", rc.headers.get("content-range","?").split("/")[-1])
print()
print("=== Conseguenza: quanti titoli restano col prezzo vecchio ===")
if isinstance(d,list):
    tot=int(rc.headers.get("content-range","0/0").split("/")[-1])
    print("  serviti col prezzo fresco : %d" % len(d))
    print("  serviti col prezzo VECCHIO: %d" % (tot-len(d)))
print()
print("=== Esempio: ASML e' tra i mille? ===")
chiavi=set("%s.%s"%(x["ticker"],x["exchange"]) for x in d) if isinstance(d,list) else set()
for k in ["ASML.AS","SAP.XETRA","MC.PA","AAPL.US","ISP.MIL"]:
    print("  %-10s %s" % (k,"si (prezzo fresco)" if k in chiavi else "NO -> mostra il prezzo vecchio"))
