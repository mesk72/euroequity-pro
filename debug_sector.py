import re, requests, json, base64
BASE="https://mlqkisnizgyvvqajdvbh.supabase.co"
r=requests.get("https://forwardalpha.pro/",timeout=30)
anon=None
for c in set(re.findall(r'/_next/static/[^"\']+?\.js[^"\']*', r.text)):
    try:
        j=requests.get("https://forwardalpha.pro"+c,timeout=20).text
        k=re.search(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}', j)
        if k: anon=k.group(); break
    except Exception: pass
H={"apikey":anon,"Authorization":"Bearer "+anon}

print("PROVA CONTROLLATA su UNA sola riga di latest_prices")
print("(uso un ticker che NON esiste: se la policy blocca, e' 401/403;")
print(" se permette, e' 204 ma con 0 righe toccate -> serve il conteggio)")
print()
# 1) quante righe ci sono ADESSO per un exchange piccolo
rc=requests.get(BASE+"/rest/v1/latest_prices",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.SGX","limit":"1"},timeout=20)
prima=rc.headers.get("content-range","?")
print("  righe SGX prima:", prima)

# 2) tento una DELETE che, se permessa, cancellerebbe DAVVERO
#    uso un filtro che matcha una riga reale ma la richiedo con return
d=requests.delete(BASE+"/rest/v1/latest_prices",
    headers={**H,"Prefer":"return=representation"},
    params={"exchange":"eq.SGX","ticker":"eq.__NON_ESISTE__"},timeout=20)
print("  DELETE su ticker inesistente -> HTTP %s, corpo: %s" % (d.status_code, d.text[:120]))

# 3) verifica che il conteggio NON sia cambiato
rc2=requests.get(BASE+"/rest/v1/latest_prices",headers={**H,"Prefer":"count=exact"},
    params={"select":"ticker","exchange":"eq.SGX","limit":"1"},timeout=20)
print("  righe SGX dopo :", rc2.headers.get("content-range","?"))

# 4) LA PROVA DECISIVA: chiedo la rappresentazione di cio' che verrebbe cancellato
#    con un filtro che matcha righe VERE. Se la policy permette, il corpo
#    conterrebbe le righe. NON eseguo se il corpo torna pieno: e' gia' la prova.
d2=requests.delete(BASE+"/rest/v1/latest_prices",
    headers={**H,"Prefer":"return=representation"},
    params={"exchange":"eq.__EXCHANGE_INESISTENTE__"},timeout=20)
print("  DELETE su exchange inesistente -> HTTP %s, corpo: %s" % (d2.status_code, d2.text[:120]))
print()
print("INTERPRETAZIONE:")
print("  se il corpo e' [] -> la DELETE e' ACCETTATA ma non tocca nulla")
print("     (policy assente = nessuna riga corrisponde alla condizione)")
print("  se fosse 401/403 -> policy che blocca esplicitamente")
