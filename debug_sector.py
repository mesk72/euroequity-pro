import os, requests, csv, io
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').replace('x','').strip()
    if s in ("","-","NM","NA","n/a"): return None
    try: return float(s)
    except: return None
PAROLE=["ETF","ETP","FUND","TRUST","UCITS","ISHARES","VANGUARD","XTRACKERS","LYXOR",
        "INVESCO","SPDR","WISDOMTREE","VANECK","BLACKROCK","SICAV","ICAV","MSCI","INDEX",
        "AMUNDI","KAPITALFORENINGEN","INVESTERINGSSELSKABET","INVESTERINGSFORENINGEN",
        "BANKINVEST","NORDEA INVEST","SYDINVEST","SPARINVEST","NYKREDIT INVEST",
        "LÅN & SPAR INVEST","SOCIMI"]
def fondo(*n): return any(any(p in (x or "").upper() for p in PAROLE) for x in n)

def tutte(tab,campi):
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":campi,"limit":"1000","offset":str(off)},timeout=90).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o
fu=tutte("fundamentals","ticker,exchange,mkt_cap")
mc={(x["ticker"],x["exchange"]):x.get("mkt_cap") for x in fu}
st=tutte("stocks","ticker,exchange,company,in_universe")

print("=== soglia 300 MM per Danimarca e Norvegia ===")
for ex,nome in [("CPSE","Danimarca"),("OB","Norvegia")]:
    dentro=ent=esc=0; fondi=0
    for x in [s for s in st if s["exchange"]==ex]:
        v=mc.get((x["ticker"],ex))
        if v is None: continue
        e_f=fondo(x.get("company"))
        vuole = (v>=300) and not e_f
        ha = bool(x.get("in_universe"))
        if vuole and not ha:
            requests.patch(U+"/rest/v1/stocks",headers=HP,
                params={"ticker":"eq."+x["ticker"],"exchange":"eq."+ex},json={"in_universe":True})
            ent+=1
        elif not vuole and ha:
            requests.patch(U+"/rest/v1/stocks",headers=HP,
                params={"ticker":"eq."+x["ticker"],"exchange":"eq."+ex},json={"in_universe":False})
            esc+=1
            if e_f: fondi+=1
        if vuole: dentro+=1
    print("  %-10s in universo ora: %3d  (entrati %d, usciti %d di cui %d fondi)" % (nome,dentro,ent,esc,fondi))

print()
print("=== i titoli danesi importanti ci sono? ===")
for tk in ["MAERSK B","NSIS B","CARL B","COLO B","ROCK B","ALK B","DANSKE","NOVO B","ORSTED","TRYG","DEMANT","GMAB","VWS","PNDORA"]:
    r=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"ticker,company,in_universe","ticker":"eq."+tk,"exchange":"eq.CPSE"}).json()
    if not r: print("  %-10s NON PRESENTE IN ANAGRAFICA" % tk); continue
    x=r[0]
    v=mc.get((tk,"CPSE"))
    print("  %-10s %-32s universo=%-5s  %s MM" % (tk,(x.get("company") or "")[:32],x.get("in_universe"),v))
print()
print("=== conteggio finale ===")
tot=0
for ex in ["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    n=int(r.headers.get("content-range","0/0").split("/")[-1]); tot+=n
    if ex in ["CPSE","OB"]: print("  %-6s %4d" % (ex,n))
print("  UNIVERSO TOTALE: %d" % tot)
