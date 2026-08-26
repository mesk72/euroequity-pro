import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
HU={**H,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
riga={"ticker":"NVDA","exchange":"US","eps_fwd24":9.99,"eps_fwd36":11.11,
      "eps_growth_12_24m":0.2,"eps_growth_24_36m":0.15,"eps_cagr_2y":0.18,
      "implied_growth_10y":0.9999,"ke":0.095,"eps_ntm_dcf":7.77}
print("=== come fa lo script (senza chiave di conflitto) ===")
r=requests.post(U+"/rest/v1/fundamentals",headers=HU,json=[riga])
print("  HTTP",r.status_code,"|",r.text[:300])
print()
print("=== con la chiave di conflitto ===")
r2=requests.post(U+"/rest/v1/fundamentals?on_conflict=ticker,exchange",headers=HU,json=[riga])
print("  HTTP",r2.status_code,"|",r2.text[:300])
print()
v=requests.get(U+"/rest/v1/fundamentals",headers=H,
    params={"select":"implied_growth_10y,ke,updated_at","ticker":"eq.NVDA","exchange":"eq.US"}).json()
print("  valore ora:",v)
