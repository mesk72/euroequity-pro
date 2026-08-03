import re, requests
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
import os
SK=os.environ.get("SUPABASE_SERVICE_KEY","")
HS={"apikey":SK,"Authorization":"Bearer "+SK}

# chiave pubblica dal sito
r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
HA={"apikey":anon,"Authorization":"Bearer "+anon}

# 1) creo una riga ESCA con la chiave di servizio (dato finto, non tocca nulla di reale)
esca={"ticker":"__SECTEST__","exchange":"SGX","price":1.0,"price_date":"2020-01-01"}
c=requests.post(BASE+"/rest/v1/latest_prices?on_conflict=ticker,exchange",
    headers={**HS,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"},
    json=[esca],timeout=20)
print("creo riga esca -> HTTP", c.status_code)
ck=requests.get(BASE+"/rest/v1/latest_prices",headers=HS,
    params={"select":"ticker","ticker":"eq.__SECTEST__"},timeout=20).json()
print("esca presente:", len(ck)==1)

# 2) provo a cancellarla con la CHIAVE PUBBLICA
d=requests.delete(BASE+"/rest/v1/latest_prices",
    headers={**HA,"Prefer":"return=representation"},
    params={"ticker":"eq.__SECTEST__"},timeout=20)
print("DELETE con chiave pubblica -> HTTP %s corpo %s" % (d.status_code, d.text[:100]))

# 3) esiste ancora?
ck2=requests.get(BASE+"/rest/v1/latest_prices",headers=HS,
    params={"select":"ticker","ticker":"eq.__SECTEST__"},timeout=20).json()
ancora=len(ck2)==1
print()
print(">>> VERDETTO: la riga %s" % ("ESISTE ANCORA -> cancellazione BLOCCATA (siamo protetti)" if ancora else "E' STATA CANCELLATA -> FALLA GRAVE REALE"))

# 4) pulizia
requests.delete(BASE+"/rest/v1/latest_prices",headers=HS,params={"ticker":"eq.__SECTEST__"},timeout=20)
fin=requests.get(BASE+"/rest/v1/latest_prices",headers=HS,
    params={"select":"ticker","ticker":"eq.__SECTEST__"},timeout=20).json()
print("pulizia esca completata:", len(fin)==0)
