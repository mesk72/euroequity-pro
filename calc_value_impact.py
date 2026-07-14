import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def pct_rank(arr, val):
    below = sum(1 for x in arr if x < val)
    return round(below / len(arr) * 100)
def ey(pe):
    if pe is None or pe==0 or abs(pe)>200: return None
    return 1/pe
def by(pb):
    if pb is None or pb==0: return None
    return 1/pb

universe = set()
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","exchange":"eq.OB","in_universe":"eq.true","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    universe.update(s["ticker"] for s in batch)
    offset += 1000
    if len(batch) < 1000: break

group = []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,pe_trailing,pe_forward,pb","exchange":"eq.OB","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe: group.append(d)
    offset += 1000
    if len(batch) < 1000: break

print(f"Titoli nel gruppo Norvegia: {len(group)}")

ey_l = [ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
ey_f = [ey(d["pe_forward"]) for d in group if ey(d["pe_forward"]) is not None]
b_g  = [by(d["pb"]) for d in group if by(d["pb"]) is not None]

val_sums = []
for d in group:
    rl = pct_rank(ey_l, ey(d["pe_trailing"])) if ey(d["pe_trailing"]) is not None else None
    rf = pct_rank(ey_f, ey(d["pe_forward"])) if ey(d["pe_forward"]) is not None else None
    rb = pct_rank(b_g, by(d["pb"])) if by(d["pb"]) is not None else None
    inputs = [x for x in [rl,rf,rb] if x is not None]
    if len(inputs) >= 2:
        val_sums.append(sum(inputs))

print(f"val_sums costruiti: {len(val_sums)}")
print(f"min={min(val_sums)}, max={max(val_sums)}, media={sum(val_sums)/len(val_sums):.1f}")

for test_sum in [204, 209, 225]:
    print(f"Sum={test_sum} -> value_score={pct_rank(val_sums, test_sum)}")
