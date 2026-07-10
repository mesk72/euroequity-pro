import os, requests, csv, io
from collections import Counter
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/fiscal_year_end.csv", headers=headers_r)
reader = csv.DictReader(io.StringIO(r.text))
by_exchange = {}
for row in reader:
    ex = row["exchange"]
    by_exchange.setdefault(ex, Counter())[row["fiscal_month"]] += 1

for ex in ["TSE","SEHK","ASX","KRX","SGX","US","TSX","MIL","XETRA","PA","LSE","SWX","OM","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS"]:
    c = by_exchange.get(ex, Counter())
    total = sum(c.values())
    zero = c.get("0",0) + c.get("",0)
    print(f"{ex}: totale={total} invalidi(0/vuoto)={zero} ({100*zero/total:.0f}%)" if total else f"{ex}: NESSUNA RIGA")
