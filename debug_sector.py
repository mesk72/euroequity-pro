import os, requests, json
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K,"Content-Type":"application/json"}
r=requests.post(U+"/storage/v1/object/list/tikr-uploads",headers=H,
    json={"limit":100,"offset":0,"sortBy":{"column":"updated_at","order":"desc"}},timeout=60)
print("HTTP:",r.status_code)
for f in r.json():
    print("  %-34s %10s byte   ultimo aggiornamento: %s" % (
        f.get("name"),
        (f.get("metadata") or {}).get("size","?"),
        (f.get("updated_at") or "?")[:19]))
