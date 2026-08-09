import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for tk,ex in [("AAPL","US"),("ASML","AS"),("MSFT","US"),("ISP","MIL")]:
    r=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"mkt_cap,div_yield,pe_trailing","ticker":"eq."+tk,"exchange":"eq."+ex}).json()
    print("%-6s %s" % (tk, r))
