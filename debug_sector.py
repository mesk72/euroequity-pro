import os, requests
from collections import defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
PAROLE=["ETF","ETN"," ETP","UCITS","ISHARES","VANGUARD","XTRACKERS","LYXOR","SPDR",
        "WISDOMTREE","VANECK","BLACKROCK","SICAV","ICAV","BETASHARES","IFREEETF",
        "KAPITALFORENING","INVESTERINGSFORENING","INVESTERINGSSELSKAB","VERDIPAPIRFOND",
        "BANKINVEST","NORDEA INVEST","SYDINVEST","SPARINVEST","SPARINDEX","NYKREDIT INVEST",
        "DANSKE INVEST","JYSKE INVEST","MULTI MANAGER INVEST","FORMUEPLEJE","GUDME RAASCHOU",
        "MAJ INVEST","AMUNDI INDEX","AMUNDI EURO","AMUNDI PRIME","MULTI UNITS",
        "INVESTMENT TRUST","INCOME TRUST","TERM TRUST","QUALITY INCOME","CLOSED-END",
        "COVERED CALL","PHYSICAL URANIUM","MUNICIPAL INCOME","ACTIVE ALLOCATION",
        " FUND","FUND ","FUNDS "]
def colpito(n):
    t=(n or "").upper()
    return any(p in t for p in PAROLE)
def tutte():
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"ticker,exchange,company,in_universe","in_universe":"eq.false",
                    "limit":"1000","offset":str(off)},timeout=120).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
fuori=tutte()
dal_filtro=[x for x in fuori if colpito(x.get("company"))]
per_ex=defaultdict(list)
for x in dal_filtro: per_ex[x["exchange"]].append((x["ticker"],(x.get("company") or "")))
print("TOTALE ESCLUSI DAL FILTRO CHE HO APPLICATO: %d" % len(dal_filtro))
print()
for ex in sorted(per_ex,key=lambda e:-len(per_ex[e])):
    print("=== %s (%d) ===" % (ex,len(per_ex[ex])))
    for tk,az in sorted(per_ex[ex]):
        print("  %-12s %s" % (tk,az[:58]))
    print()
