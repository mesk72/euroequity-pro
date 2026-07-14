import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

def ey(pe):
    if pe is None or pe == 0 or abs(pe) > 200: return None
    return 1/pe

def pct_rank(arr, val):
    below = sum(1 for x in arr if x < val)
    return round(below / len(arr) * 100)

# Dati NSKOG attuali (pre-calo)
old_price = 42.9
old_pe_ltm = 10.53
old_pe_ntm = 11.21

new_price = old_price * (1 - 0.18)          # calo 18%
new_eps_ltm_factor = 1 - 0.35                # EPS LTM tagliato 35%
new_eps_ntm_factor = 1 - 0.32                # EPS NTM tagliato 32%

new_pe_ltm = old_pe_ltm * (new_price/old_price) / new_eps_ltm_factor
new_pe_ntm = old_pe_ntm * (new_price/old_price) / new_eps_ntm_factor

print(f"Nuovo prezzo stimato: {new_price:.2f} (da {old_price})")
print(f"Nuovo PE LTM stimato: {new_pe_ltm:.2f} (da {old_pe_ltm})")
print(f"Nuovo PE NTM stimato: {new_pe_ntm:.2f} (da {old_pe_ntm})")

# Distribuzione reale Norvegia
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

pe_ltm_vals, pe_ntm_vals = [], []
offset = 0
while True:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
        params={"select":"ticker,pe_trailing,pe_forward","exchange":"eq.OB","limit":"1000","offset":str(offset)})
    batch = r.json()
    if not isinstance(batch,list) or not batch: break
    for d in batch:
        if d["ticker"] in universe:
            if d.get("pe_trailing") is not None:
                v = ey(d["pe_trailing"])
                if v is not None: pe_ltm_vals.append(v)
            if d.get("pe_forward") is not None:
                v = ey(d["pe_forward"])
                if v is not None: pe_ntm_vals.append(v)
    offset += 1000
    if len(batch) < 1000: break

new_ey_ltm = ey(new_pe_ltm)
new_ey_ntm = ey(new_pe_ntm)
new_rank_ltm = pct_rank(pe_ltm_vals, new_ey_ltm)
new_rank_ntm = pct_rank(pe_ntm_vals, new_ey_ntm)

print(f"\nNuovo rank_pe_ltm: {new_rank_ltm} (prima: 69)")
print(f"Nuovo rank_pe_ntm: {new_rank_ntm} (prima: 58)")
