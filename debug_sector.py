import os, requests
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
def parola(n):
    t=(n or "").upper()
    return [p for p in PAROLE if p in t]

def tutte(ex):
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"ticker,company,in_universe","exchange":"eq."+ex,
                    "in_universe":"eq.false","limit":"1000","offset":str(off)},timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o

for ex,nome in [("US","STATI UNITI"),("LSE","REGNO UNITO")]:
    fuori=tutte(ex)
    # solo quelli esclusi DAL FILTRO (nome che contiene una parola chiave)
    dal_filtro=[(x["ticker"],(x.get("company") or ""),parola(x.get("company"))) for x in fuori if parola(x.get("company"))]
    print("=== %s: %d esclusi dal filtro fondi ===" % (nome,len(dal_filtro)))
    for tk,az,pp in sorted(dal_filtro):
        print("  %-10s %-52s [%s]" % (tk,az[:52],pp[0]))
    print()
