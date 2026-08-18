import os, requests, csv, io
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for f in ["tikr_eu_latest.csv","tikr_na_latest.csv"]:
    print("=== %s ===" % f)
    r=requests.get(U+"/storage/v1/object/tikr-uploads/"+f,headers=H,timeout=120)
    if r.status_code!=200:
        print("  HTTP",r.status_code); continue
    txt=r.content.decode("utf-8",errors="replace")
    rd=list(csv.DictReader(io.StringIO(txt)))
    print("  righe:",len(rd))
    cols=[c for c in rd[0].keys() if "Mkt Cap" in c or "Ticker" in c or "Name" in c]
    print("  colonne rilevanti:",cols)
    print()
    print("  ESEMPI (societa' note, per capire l'unita'):")
    n=0
    for row in rd:
        nome=(row.get("Company Name") or row.get("Name") or "")
        if any(k in nome.upper() for k in ["ASML","SAP ","NESTLE","NESTLÉ","LVMH","NORSKE","NEOBO","NIVIKA","YOUGOV"]):
            print("   %-34s Last Mkt Cap = %s" % (nome[:34], row.get("Last Mkt Cap")))
            n+=1
            if n>=8: break
    print()
    vals=[]
    for row in rd:
        v=row.get("Last Mkt Cap","").replace(",","").strip()
        try: vals.append(float(v))
        except Exception: pass
    if vals:
        vals.sort()
        print("  distribuzione: min=%.4f  mediana=%.2f  max=%.0f" % (vals[0],vals[len(vals)//2],vals[-1]))
        print("  quanti sotto 1:", sum(1 for v in vals if v<1))
    print()
