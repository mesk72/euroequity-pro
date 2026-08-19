import os, requests, csv, io
from collections import Counter
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
r=requests.get(U+"/storage/v1/object/tikr-uploads/tikr_eu_latest.csv",headers=H,timeout=150)
righe=list(csv.DictReader(io.StringIO(r.content.decode("utf-8",errors="replace"))))
print("righe TIKR EU:",len(righe))
print("colonne:",list(righe[0].keys())[:12])
print()
print("=== come sono scritti i ticker? primi 15 ===")
for row in righe[:15]:
    print("   Ticker=%-18s  Exchange=%-12s  %s" % (
        (row.get("Ticker") or "")[:18],
        (row.get("Exchange") or row.get("Exchange:Ticker") or "?")[:12],
        (row.get("Company Name") or "")[:34]))
print()
print("=== esempi nordici ===")
for row in righe:
    n=(row.get("Company Name") or "")
    if any(k in n for k in ["Norske Skog","Neobo","Nivika","Hexagon Composites","Zalaris"]):
        print("   %-20s %-34s %s" % (row.get("Ticker"), n[:34], row.get("Last Mkt Cap")))
print()
c=Counter()
for row in righe:
    t=(row.get("Ticker") or "")
    c["."+t.split(".")[-1] if "." in t else "senza punto"]+=1
print("=== suffissi presenti ===")
for k,v in c.most_common(20): print("   %-10s %d" % (k,v))
