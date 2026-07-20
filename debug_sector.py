import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Approssimazione S&P 500: top 500 US per market cap (non e' identico
# alla vera composizione S&P, che ha criteri propri, ma e' la stima
# standard quando non abbiamo il file di composizione ufficiale)
all_rows = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,mkt_cap,implied_growth_10y","exchange":"eq.US",
                 "mkt_cap":"not.is.null","implied_growth_10y":"not.is.null",
                 "limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    all_rows.extend(batch)
    offset += 1000
    if len(batch) < 1000: break

sorted_rows = sorted(all_rows, key=lambda x: x["mkt_cap"], reverse=True)
top500 = sorted_rows[:500]

total_cap = sum(r["mkt_cap"] for r in top500)
wsum = sum(r["implied_growth_10y"] * r["mkt_cap"] for r in top500)
wg_500 = wsum / total_cap

print(f"S&P 500 (approssimato: top 500 US per market cap), {len(top500)} titoli")
print(f"Implied Growth 10Y medio (weighted by mkt cap): {round(wg_500*100,2)}%")
print(f"Mkt cap totale: ${total_cap/1000:.1f}B")
print(f"\nConfronto:")
print(f"  Dow Jones (30 titoli, pesi indice): 8.12%")
print(f"  S&P 500 (top 500 mkt cap): {round(wg_500*100,2)}%")
print(f"  Differenza: {round((wg_500*100)-8.12,2)} punti percentuali")
