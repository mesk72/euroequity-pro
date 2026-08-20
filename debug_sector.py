import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K,"Content-Type":"application/json"}
r=requests.post(U+"/storage/v1/object/list/tikr-uploads",headers=H,
    json={"prefix":"","limit":100,"offset":0},timeout=60)
print("HTTP:",r.status_code)
if r.status_code!=200:
    print(r.text[:300])
else:
    for f in r.json():
        md=f.get("metadata") or {}
        print("  %-36s %12s byte  %s" % (f.get("name"), md.get("size","?"), (f.get("updated_at") or "?")[:19]))
print()
print("=== quali nomi rispondono davvero? ===")
for n in ["tikr_eu_latest.csv","tikr_na_latest.csv","tikr_apac_latest.csv",
          "tikr_upload_na.csv","tikr_prod_europa.csv","tikr_asia_pacific.csv",
          "fiscal_year_end.csv"]:
    rr=requests.head(U+"/storage/v1/object/tikr-uploads/"+n,headers={"apikey":K,"Authorization":"Bearer "+K},timeout=30)
    print("   %-28s HTTP %s" % (n, rr.status_code))
