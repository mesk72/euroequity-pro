import os, requests
from collections import defaultdict
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}

# Fondi ed ETF certi. Volutamente prudente: meglio tenere per errore un
# veicolo che perdere una societa' operativa.
PAROLE=["ETF","ETN"," ETP","UCITS","ISHARES","VANGUARD","XTRACKERS","LYXOR","SPDR",
        "WISDOMTREE","VANECK","BLACKROCK","SICAV","ICAV","BETASHARES","IFREEETF",
        "KAPITALFORENING","INVESTERINGSFORENING","INVESTERINGSSELSKAB","VERDIPAPIRFOND",
        "BANKINVEST","NORDEA INVEST","SYDINVEST","SPARINVEST","SPARINDEX","NYKREDIT INVEST",
        "DANSKE INVEST","JYSKE INVEST","MULTI MANAGER INVEST","FORMUEPLEJE","GUDME RAASCHOU",
        "MAJ INVEST","AMUNDI INDEX","AMUNDI EURO","AMUNDI PRIME","MULTI UNITS",
        "INVESTMENT TRUST","INCOME TRUST","TERM TRUST","QUALITY INCOME","CLOSED-END",
        "COVERED CALL","PHYSICAL URANIUM","MUNICIPAL INCOME","ACTIVE ALLOCATION"]
# Non bastano da sole: la parola "FUND" compare in societa' operative
# (FleetPartners, Rural Funds) e in REIT che restano dentro per scelta.
SOLO_SE_FONDO=[" FUND", "FUND ", "FUNDS "]
# Mai escludere: falsi positivi verificati a mano il 20/8/2026.
MAI=[("AMUN","PA"),      # Amundi S.A.: societa' di gestione quotata, 10 mld
     ("LINDEX","HE"),    # Lindex Group: catena di abbigliamento, "index" e' dentro il nome
     ("FPR","ASX")]      # FleetPartners Group: societa' operativa
# I REIT restano DENTRO per decisione di Andrea: sono veicoli immobiliari
# ma anche societa' operative, e molti indici li includono (MERLIN
# Properties e' nell'IBEX 35).
REIT=["SOCIMI","REAL ESTATE","REIT","PROPERTIES","BUILDING FUND","LOGISTICS FUND",
      "METROPOLITAN FUND","MASTER FUND","INFRASTRUCTURE FUND","ACCOMMODATIONS FUND",
      "INFRASTRUKTUR"]

def e_reit(n): return any(p in n for p in REIT)
def da_escludere(ticker,exchange,nome):
    if (ticker,exchange) in MAI: return False
    n=(nome or "").upper()
    if e_reit(n): return False
    if any(p in n for p in PAROLE): return True
    if any(p in n for p in SOLO_SE_FONDO): return True
    return False

def tutte(tab,campi):
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/"+tab,headers=H,params={"select":campi,"limit":"1000","offset":str(off)},timeout=120).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    return o

st=tutte("stocks","ticker,exchange,company,in_universe")
tolti=defaultdict(list)
for x in st:
    if not x.get("in_universe"): continue
    if da_escludere(x["ticker"],x["exchange"],x.get("company")):
        tolti[x["exchange"]].append((x["ticker"],(x.get("company") or "")[:44]))
tot=sum(len(v) for v in tolti.values())
print("=== ESCLUSIONI: %d ===" % tot)
for ex in sorted(tolti,key=lambda e:-len(tolti[e])):
    print("  %-6s %3d" % (ex,len(tolti[ex])))
print()
print("Applico...")
n=0
for ex,lista in tolti.items():
    for tk,_ in lista:
        r=requests.patch(U+"/rest/v1/stocks",headers=HP,
            params={"ticker":"eq."+tk,"exchange":"eq."+ex},json={"in_universe":False})
        if r.status_code==204: n+=1
print("  esclusi: %d" % n)

print()
print("=== Danimarca SENZA soglia: reintegro le societa' operative ===")
fu=tutte("fundamentals","ticker,exchange,mkt_cap")
mc={(x["ticker"],x["exchange"]):x.get("mkt_cap") for x in fu}
ent=0
for x in st:
    if x["exchange"]!="CPSE" or x.get("in_universe"): continue
    if da_escludere(x["ticker"],"CPSE",x.get("company")): continue
    r=requests.patch(U+"/rest/v1/stocks",headers=HP,
        params={"ticker":"eq."+x["ticker"],"exchange":"eq.CPSE"},json={"in_universe":True})
    if r.status_code==204:
        ent+=1
        print("   rientra %-12s %-42s %s MM" % (x["ticker"],(x.get("company") or "")[:42],mc.get((x["ticker"],"CPSE"))))
print("  rientrati: %d" % ent)

print()
print("=== CONTEGGIO FINALE ===")
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]
tot=0
for ex in EX:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    v=int(r.headers.get("content-range","0/0").split("/")[-1]); tot+=v
    print("  %-6s %4d" % (ex,v))
print("  TOTALE: %d" % tot)
