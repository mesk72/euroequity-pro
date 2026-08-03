import os, requests, re
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
SK=os.environ.get("SUPABASE_SERVICE_KEY","")
HS={"apikey":SK,"Authorization":"Bearer "+SK}
r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
HA={"apikey":anon,"Authorization":"Bearer "+anon,"Content-Type":"application/json"}

print("PROVA REALE con la chiave pubblica del sito")
print("(riga esca creata con chiave di servizio, poi tento di alterarla da anonimo)")
print()

def prova(tab, esca, chiave_filtro):
    # crea esca
    requests.post(BASE+"/rest/v1/"+tab+"?on_conflict="+chiave_filtro,
        headers={**HS,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"},
        json=[esca],timeout=25)
    f={k:"eq."+str(v) for k,v in esca.items() if k in chiave_filtro.split(",")}
    esiste=lambda: len(requests.get(BASE+"/rest/v1/"+tab,headers=HS,params={**f,"select":"*"},timeout=25).json())>0
    if not esiste():
        print("  %-24s (impossibile creare esca, salto)" % tab); return
    # UPDATE anonimo
    u=requests.patch(BASE+"/rest/v1/"+tab,headers=HA,params=f,json={"exchange":esca["exchange"]},timeout=25)
    # DELETE anonimo
    d=requests.delete(BASE+"/rest/v1/"+tab,headers=HA,params=f,timeout=25)
    sopravvissuta=esiste()
    print("  %-24s UPDATE:%s  DELETE:%s  -> %s" % (
        tab,u.status_code,d.status_code,
        "PROTETTA" if sopravvissuta else "!!! DATI CANCELLABILI DA CHIUNQUE !!!"))
    # pulizia
    requests.delete(BASE+"/rest/v1/"+tab,headers=HS,params=f,timeout=25)

prova("latest_prices",{"ticker":"__SEC__","exchange":"SGX","price":1.0,"price_date":"2020-01-01"},"ticker,exchange")
prova("stocks",{"ticker":"__SEC__","exchange":"SGX"},"ticker,exchange")
prova("prices_eod",{"ticker":"__SEC__","exchange":"SGX","date":"2020-01-01","adj_close":1.0},"ticker,exchange,date")
prova("sector_quintile_partials",{"exchange":"__SEC__","sector":"__SEC__"},"exchange,sector")
