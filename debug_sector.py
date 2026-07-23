import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.9984","exchange":"eq.TSE","order":"date.desc","limit":"5"})
print("Ultimi 5 prezzi reali per 9984.TSE:")
for row in r.json():
    print(" ", row)

r2 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,price,change1d","ticker":"eq.9984","exchange":"eq.TSE"})
print("\nCampo fundamentals.price (statico, potrebbe essere una terza fonte):", r2.json())
