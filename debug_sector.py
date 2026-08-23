import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
EX=[("MIL","Italia"),("XETRA","Germania"),("PA","Francia"),("AS","Paesi Bassi"),
    ("MC","Spagna"),("BR","Belgio"),("LS","Portogallo"),("VI","Austria"),
    ("HE","Finlandia"),("IR","Irlanda"),("GR","Grecia"),("LSE","Regno Unito"),
    ("SWX","Svizzera"),("OM","Svezia"),("OB","Norvegia"),("CPSE","Danimarca"),
    ("US","Stati Uniti"),("TSX","Canada"),("TSE","Giappone"),("SEHK","Hong Kong"),
    ("ASX","Australia"),("KRX","Corea"),("SGX","Singapore")]
tot=0; eu=0; na=0; ap=0
print("%-14s %-6s %6s" % ("PAESE","COD","TITOLI"))
for ex,nome in EX:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    n=int(r.headers.get("content-range","0/0").split("/")[-1]); tot+=n
    if ex in ["US","TSX"]: na+=n
    elif ex in ["TSE","SEHK","ASX","KRX","SGX"]: ap+=n
    else: eu+=n
    print("%-14s %-6s %6d" % (nome,ex,n))
print()
print("  Europa           %5d" % eu)
print("  Nord America     %5d" % na)
print("  Asia Pacifico    %5d" % ap)
print("  ---------------------")
print("  GLOBAL           %5d" % tot)
print()
# quanti hanno prezzo e punteggi
mv=0; vs=0
for ex,_ in EX:
    r=requests.get(U+"/rest/v1/latest_prices_mv",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"limit":"1"})
    mv+=int(r.headers.get("content-range","0/0").split("/")[-1])
print("  righe nella vista prezzi: %d" % mv)
