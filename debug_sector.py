import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

EUROPE = "MIL,XETRA,PA,AS,MC,BR,LS,VI,HE,IR,GR,LSE,SWX,OM,OB,CPSE"

sectors = ["Information Technology", "Financials", "Healthcare"]

print("=== Conteggio Europa (16 mercati, NGM escluso, in_universe=true) ===")
print("Stesso identico filtro usato ora da: SectorScreen, pagina Sectors, popup Sector Comparison\n")

for sec in sectors:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","exchange":f"in.({EUROPE})","sector":f"eq.{sec}","in_universe":"eq.true"})
    count = r.headers.get("content-range","").split("/")[-1]
    print(f"{sec}: {count} titoli")

# Verifica extra: conferma che NGM sia davvero escluso (differenza rispetto a includerlo)
print("\n=== Controllo di sicurezza: quanti NGM ci sarebbero se INCLUSI per errore ===")
for sec in sectors:
    r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
        params={"select":"ticker","exchange":"eq.NGM","sector":f"eq.{sec}","in_universe":"eq.true"})
    count_ngm = r2.headers.get("content-range","").split("/")[-1]
    print(f"  {sec} su NGM: {count_ngm} (questi NON devono essere contati)")
