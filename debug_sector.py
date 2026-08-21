import os, requests, json
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
            params={"select":"ticker,exchange,company,sector","in_universe":"eq.false",
                    "limit":"1000","offset":str(off)},timeout=120).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
fu=[];off=0
while True:
    b=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"ticker,exchange,mkt_cap","limit":"1000","offset":str(off)},timeout=120).json()
    if not isinstance(b,list) or not b: break
    fu+=b; off+=1000
    if len(b)<1000: break
mc={(x["ticker"],x["exchange"]):x.get("mkt_cap") for x in fu}
esclusi=[x for x in tutte() if colpito(x.get("company"))]
righe=[]
for x in esclusi:
    righe.append({"ticker":x["ticker"],"exchange":x["exchange"],
                  "company":(x.get("company") or ""),"sector":(x.get("sector") or ""),
                  "mkt_cap":mc.get((x["ticker"],x["exchange"]))})
righe.sort(key=lambda z:(z["exchange"],-(z["mkt_cap"] or 0)))
print(json.dumps(righe,ensure_ascii=False))
