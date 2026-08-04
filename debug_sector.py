import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
print("=== Quante righe torna la query di fetchLatestPrices SENZA paginazione? ===")
for exlist,eti in [(["US"],"solo US (in DB: 3001)"),
                   (["US","TSX"],"US+TSX"),
                   (["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"],"Europa (in DB: ~2126)")]:
    inlist="(" + ",".join(exlist) + ")"
    r=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"ticker,exchange,price,price_date,change1d","exchange":"in."+inlist})
    n=len(r.json()) if isinstance(r.json(),list) else 0
    print("  %-26s -> %d righe restituite" % (eti,n))

print()
print("=== Conseguenza: quanti titoli US NON ricevono il prezzo fresco ===")
rc=requests.get(U+"/rest/v1/latest_prices",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.US","limit":"1"})
tot=int(rc.headers.get("content-range","0/0").split("/")[-1])
print("  righe reali in latest_prices per US:",tot)
print("  righe che il sito riesce a leggere: 1000 (limite PostgREST)")
print("  titoli che ricadono su fundamentals/stocks:",tot-1000)
