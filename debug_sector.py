import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

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

print(f"Totale titoli US con mkt_cap e implied_growth_10y validi: {len(all_rows)}")

sorted_rows = sorted(all_rows, key=lambda x: x["mkt_cap"], reverse=True)

top1000 = sorted_rows[:1000]
rest = sorted_rows[1000:]

def weighted_avg_ig(rows):
    total_cap = sum(r["mkt_cap"] for r in rows)
    if total_cap == 0: return None
    wsum = sum(r["implied_growth_10y"] * r["mkt_cap"] for r in rows)
    return wsum / total_cap

wg_top = weighted_avg_ig(top1000)
wg_rest = weighted_avg_ig(rest)

print(f"\nTop 1000 per market cap ({len(top1000)} titoli):")
print(f"  Implied Growth 10Y medio (weighted by mkt cap): {round(wg_top*100,2)}%")
print(f"  Mkt cap totale gruppo: ${sum(r['mkt_cap'] for r in top1000)/1000:.1f}B")

print(f"\nRestanti ({len(rest)} titoli):")
print(f"  Implied Growth 10Y medio (weighted by mkt cap): {round(wg_rest*100,2)}%")
print(f"  Mkt cap totale gruppo: ${sum(r['mkt_cap'] for r in rest)/1000:.1f}B")
