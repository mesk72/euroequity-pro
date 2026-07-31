import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
EU=["MIL","XETRA","PA","AS","MC","BR","LS","VI","HE","IR","GR","LSE","SWX","OM","OB","CPSE"]

da_sistemare=[]
for ex in EU:
    r=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"ticker","exchange":"eq."+ex,"price_date":"eq.2026-07-30","limit":"1000"})
    for x in r.json(): da_sistemare.append((x["ticker"],ex))
print("Righe in cache ancora al 30/07 (ormai inesistente nei dati grezzi): %d" % len(da_sistemare))

agg=0; senza=0
batch=[]
for tk,ex in da_sistemare:
    r=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,
                "order":"date.desc","limit":"2"})
    rows=r.json()
    if not isinstance(rows,list) or not rows:
        senza+=1; continue
    ult=rows[0]; prec=rows[1] if len(rows)>1 else None
    chg=round(ult["adj_close"]/prec["adj_close"]-1,6) if (prec and prec.get("adj_close")) else None
    pp=(ult["adj_close"]/(1+chg)) if (chg is not None and (1+chg)!=0) else None
    batch.append({"ticker":tk,"exchange":ex,"price":ult["adj_close"],
                  "prev_price":pp,"price_date":ult["date"],"change1d":chg})

for i in range(0,len(batch),500):
    r=requests.post(U+"/rest/v1/latest_prices?on_conflict=ticker,exchange",headers=HU,json=batch[i:i+500])
    if r.status_code in (200,201,204): agg+=len(batch[i:i+500])
    else: print("  ERRORE HTTP %s: %s" % (r.status_code, r.text[:150]))

print("Riallineate: %d   senza dato grezzo: %d" % (agg,senza))

print("\nControllo finale: righe europee ancora al 30/07 in cache")
res=0
for ex in EU:
    r=requests.get(U+"/rest/v1/latest_prices",headers={**H,"Prefer":"count=exact"},
        params={"select":"ticker","exchange":"eq."+ex,"price_date":"eq.2026-07-30","limit":"1"})
    res+=int(r.headers.get("content-range","0/0").split("/")[-1])
print("  residue: %d" % res)

print("\nCoerenza grezzo/cache su 3 titoli:")
for tk,ex in [("AKTIA","HE"),("BURE","OM"),("ALMB","CPSE")]:
    a=requests.get(U+"/rest/v1/prices_eod",headers=H,
        params={"select":"date,adj_close","ticker":"eq."+tk,"exchange":"eq."+ex,"order":"date.desc","limit":"1"}).json()
    b=requests.get(U+"/rest/v1/latest_prices",headers=H,
        params={"select":"price_date,price","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    print("  %-6s.%-5s grezzo=%s  cache=%s" % (tk,ex,
        (a[0]["date"],a[0]["adj_close"]) if a else "-",
        (b[0]["price_date"],b[0]["price"]) if b else "-"))
