import os, requests, csv, io, time
import yfinance as yf
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
def pn(v):
    s=str(v).replace('$','').replace('MM','').replace(',','').replace('x','').strip()
    try: return float(s)
    except: return None

# cosa dice TIKR per questi titoli
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
col=[c for c in righe[0].keys()]
pe_col=[c for c in col if "P/E" in c or "PE " in c]
pb_col=[c for c in col if "P/BV" in c or "P/B" in c]
print("colonne P/E in TIKR:", pe_col[:4])
print("colonne P/B in TIKR:", pb_col[:4])
print()
idx={}
for row in righe:
    t=(row.get("Ticker") or "").strip()
    px=(row.get("Primary Exchange") or "").strip()
    if t: idx[(t,px)]=row

print("%-9s %-30s %-22s %-22s %s" % ("TICKER","SOCIETA'","NOSTRO DB","TIKR","YAHOO"))
for tk,px,ex,yt in [("GSF","OB","OB","GSF.OL"),("PEN","OB","OB","PEN.OL"),
                    ("AKAST","OB","OB","AKAST.OL"),("OKEA","OB","OB","OKEA.OL"),
                    ("CARL B","CPSE","CPSE","CARL-B.CO")]:
    f=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"pe_trailing,pb","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    nostro="PE=%s PB=%s" % (f[0].get("pe_trailing"),f[0].get("pb")) if f else "-"
    row=idx.get((tk,px))
    tk_pe=pn(row.get(pe_col[0])) if row and pe_col else None
    tk_pb=pn(row.get(pb_col[0])) if row and pb_col else None
    tikr_s="PE=%s PB=%s" % (tk_pe,tk_pb)
    try:
        info=yf.Ticker(yt).info
        ypе=info.get("trailingPE"); ypb=info.get("priceToBook")
        yah="PE=%s PB=%s" % (round(ypе,2) if ypе else None, round(ypb,2) if ypb else None)
    except Exception as e:
        yah="errore"
    nome=(row.get("Company Name") if row else "")[:30]
    print("%-9s %-30s %-22s %-22s %s" % (tk,nome,nostro,tikr_s,yah))
    time.sleep(0.6)
