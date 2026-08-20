import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}

# Riconosce fondi e veicoli, non solo dal nome inglese ma dalle forme
# usate nei paesi nordici e latini.
PAROLE=["ETF","ETP","UCITS","ISHARES","VANGUARD","XTRACKERS","LYXOR","INVESCO","SPDR",
        "WISDOMTREE","VANECK","BLACKROCK","SICAV","ICAV","INDEX","INDEKS","AMUNDI",
        "KAPITALFORENING","INVESTERINGSFORENING","INVESTERINGSSELSKAB","VERDIPAPIRFOND",
        "BANKINVEST","NORDEA INVEST","SYDINVEST","SPARINVEST","SPARINDEX","NYKREDIT INVEST",
        "DANSKE INVEST","JYSKE INVEST","MULTI MANAGER INVEST","FORMUEPLEJE","GUDME RAASCHOU",
        "MAJ INVEST","LÅN & SPAR INVEST","LAN & SPAR INVEST","EGNSINVEST",
        " FUND","FUND ","FONDS","FONDEN","SOCIMI","REIT ETF"]
def fondo(nome):
    n=(nome or "").upper()
    return any(p in n for p in PAROLE)

def tutte(tab,campi,extra=None):
    o=[];off=0
    while True:
        p={"select":campi,"limit":"1000","offset":str(off)}
        if extra: p.update(extra)
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params=p,timeout=120).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
st=tutte("stocks","ticker,exchange,company,in_universe")
print("=== PROVA DEL FILTRO: cosa escluderebbe, mercato per mercato ===")
print("(solo titoli attualmente IN universo)\n")
from collections import defaultdict
tolti=defaultdict(list)
for x in st:
    if not x.get("in_universe"): continue
    if fondo(x.get("company")):
        tolti[x["exchange"]].append((x["ticker"],(x.get("company") or "")[:46]))
tot=0
for ex in sorted(tolti,key=lambda e:-len(tolti[e])):
    print("  %-6s %3d" % (ex,len(tolti[ex]))); tot+=len(tolti[ex])
    for t,n in tolti[ex][:10]:
        print("       %-12s %s" % (t,n))
    if len(tolti[ex])>10: print("       ...e altri %d" % (len(tolti[ex])-10))
print("\n  TOTALE che verrebbero esclusi: %d" % tot)
