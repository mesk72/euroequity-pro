import os, requests, csv, io
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/storage/v1/object/tikr-uploads/fiscal_year_end.csv",headers=H,timeout=200)
print("HTTP:",r.status_code,"| byte:",len(r.content))
if r.status_code==200:
    txt=r.content.decode("utf-8",errors="replace")
    righe=list(csv.DictReader(io.StringIO(txt)))
    print("righe:",len(righe))
    print("colonne:",list(righe[0].keys()) if righe else "-")
    print()
    for x in righe[:5]: print("  ",x)
