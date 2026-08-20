import os, requests, csv, io
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for f in ["tikr_eu_latest.csv","tikr_na_latest.csv"]:
    r=requests.get(U+"/storage/v1/object/tikr-uploads/"+f,headers=H,timeout=150)
    if r.status_code!=200: print(f,"HTTP",r.status_code); continue
    righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
    print("=== %s : %d righe ===" % (f,len(righe)))
    for i,c in enumerate(righe[0].keys()): print("  %2d  %s" % (i,c))
    print()
    break
