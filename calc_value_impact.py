import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def pct_rank(arr, val):
    if val is None or not arr: return None
    below = sum(1 for x in arr if x < val)
    return round(below / len(arr) * 100)

def ey(pe):
    if pe is None or pe == 0 or abs(pe) > 200: return None
    return 1/pe

def book_yield(pb):
    if pb is None or pb == 0: return None
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
        if d["ticker"] in universe:
            group.append(d)
    offset += 1000
    if len(batch) < 1000: break

ey_trail_g = [ey(d["pe_trailing"]) for d in group if ey(d["pe_trailing"]) is not None]
ey_fwd_g   = [ey(d["pe_forward"])  for d in group if ey(d["pe_forward"])  is not None]
by_g       = [book_yield(d["pb"])  for d in group if book_yield(d["pb"])  is not None]

val_sums = []
for d in group:
    ey_t = ey(d["pe_trailing"]); r_eyt = pct_rank(ey_trail_g, ey_t) if ey_t is not None else None
    ey_f = ey(d["pe_forward"]);  r_eyf = pct_rank(ey_fwd_g,   ey_f) if ey_f is not None else None
    by_v = book_yield(d["pb"]);  r_pb  = pct_rank(by_g,       by_v) if by_v is not None else None
    inputs = [x for x in [r_eyt, r_eyf, r_pb] if x is not None]
    if len(inputs) >= 2:
        val_sums.append(sum(inputs))

print(f"Titoli con val_sums valido: {len(val_sums)}")

old_sum = 69 + 58 + 98
new_sum = 48 + 63 + 98  # PB rank invariato a 98, come da tua domanda

old_value_score = pct_rank(val_sums, old_sum)
new_value_score = pct_rank(val_sums, new_sum)

print(f"\nSomma rank PRIMA (LTM=69+NTM=58+PB=98={old_sum}): value_score ricalcolato = {old_value_score}")
print(f"  (tu avevi detto 85 — confronto per verificare coerenza)")
print(f"\nSomma rank DOPO (LTM=48+NTM=63+PB=98={new_sum}): value_score = {new_value_score}")
print(f"\nImpatto: {new_value_score - old_value_score:+d} punti")
