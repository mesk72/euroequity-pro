import os, requests
U="https://mlqkisnizgyvvqajdvbh.supabase.co"
K=os.environ.get("SUPABASE_SERVICE_KEY","")
H={"apikey":K,"Authorization":"Bearer "+K}
for tk in ["NVDA","AAPL","MSFT"]:
    f=requests.get(U+"/rest/v1/fundamentals",headers=H,
        params={"select":"price","ticker":"eq."+tk,"exchange":"eq.US"}).json()
    v=requests.get(U+"/rest/v1/latest_prices_mv",headers=H,
        params={"select":"price,price_date","ticker":"eq."+tk,"exchange":"eq.US"}).json()
    print("  %-6s fundamentals.price=%-10s | vista=%s" % (tk,
        f[0].get("price") if f else "-", v[0] if v else "-"))
