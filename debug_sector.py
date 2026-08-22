import os, requests, json, re, time
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HP={**H,"Content-Type":"application/json"}
d=json.load(open('/home/claude/dati210.json')) if os.path.exists('/home/claude/dati210.json') else None
if d is None:
    # ricostruisco l'elenco dal database
    PAROLE=["ETF","ETN"," ETP","UCITS","ISHARES","VANGUARD","XTRACKERS","LYXOR","SPDR",
            "WISDOMTREE","VANECK","BLACKROCK","SICAV","ICAV","BETASHARES","IFREEETF",
            "KAPITALFORENING","INVESTERINGSFORENING","INVESTERINGSSELSKAB","VERDIPAPIRFOND",
            "BANKINVEST","NORDEA INVEST","SYDINVEST","SPARINVEST","SPARINDEX","NYKREDIT INVEST",
            "DANSKE INVEST","JYSKE INVEST","MULTI MANAGER INVEST","FORMUEPLEJE","GUDME RAASCHOU",
            "MAJ INVEST","AMUNDI INDEX","AMUNDI EURO","AMUNDI PRIME","MULTI UNITS",
            "INVESTMENT TRUST","INCOME TRUST","TERM TRUST","QUALITY INCOME","CLOSED-END",
            "COVERED CALL","PHYSICAL URANIUM","MUNICIPAL INCOME","ACTIVE ALLOCATION",
            " FUND","FUND ","FUNDS "]
    o=[];off=0
    while True:
        b=requests.get(U+"/rest/v1/stocks",headers=H,
            params={"select":"ticker,exchange,company","in_universe":"eq.false",
                    "limit":"1000","offset":str(off)},timeout=120).json()
        if not isinstance(b,list) or not b: break
        o+=b; off+=1000
        if len(b)<1000: break
    d=[x for x in o if any(p in (x.get("company") or "").upper() for p in PAROLE)]
print("candidati: %d" % len(d))

def fuori(nome):
    t=(nome or "").upper()
    parole=set(re.findall(r"[A-Z0-9&]+",t))
    if parole & {"ETF","ETP","ETN","FUND","FUNDS","INDEX","INDEKS"}: return True
    if re.search(r"[a-z]ETF\b", nome or ""): return True
    if "INVEST" in parole: return True
    if re.search(r"\b(BANKINVEST|SYDINVEST|SPARINVEST|SPARINDEX|EGNSINVEST|MAJINVEST)\b",t): return True
    return False

back=[x for x in d if not fuori(x.get("company"))]
print("da reintegrare: %d" % len(back))
ok=0; falliti=[]
for x in back:
    for tentativo in range(3):
        try:
            r=requests.patch(U+"/rest/v1/stocks",headers=HP,
                params={"ticker":"eq."+x["ticker"],"exchange":"eq."+x["exchange"]},
                json={"in_universe":True},timeout=30)
            if r.status_code==204: ok+=1; break
        except Exception:
            time.sleep(1)
    else:
        falliti.append((x["ticker"],x["exchange"]))
print("reintegrati: %d | falliti: %d" % (ok,len(falliti)))
if falliti: print("  ",falliti[:10])
print()
print("=== verifica ===")
for tk,ex in [("SMT","LSE"),("ALLFG","AS"),("BST","US"),("NFLX","US"),("1305","TSE"),("DKIGI","CPSE")]:
    v=requests.get(U+"/rest/v1/stocks",headers=H,
        params={"select":"company,in_universe","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    if v: print("  %-9s %-44s %s" % (tk,(v[0].get('company') or '')[:44],
        "dentro" if v[0].get("in_universe") else "FUORI"))
EX=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE","US","TSX","TSE","SEHK","ASX","KRX","SGX"]
tot=0
for ex in EX:
    r=requests.get(U+"/rest/v1/stocks",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"in_universe":"eq.true","limit":"1"})
    tot+=int(r.headers.get("content-range","0/0").split("/")[-1])
print("\nUNIVERSO TOTALE: %d" % tot)
