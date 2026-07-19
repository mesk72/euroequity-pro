import os, requests, datetime
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    import subprocess
    subprocess.run(["pip","install","python-dateutil","--break-system-packages","-q"])
    from dateutil.relativedelta import relativedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
    params={"select":"date,adj_close","ticker":"eq.SIE","exchange":"eq.XETRA","order":"date.desc","limit":"800"})
prices = r.json()
print(f"Siemens (SIE.XETRA) - dati disponibili: {len(prices)} righe")
today_str = prices[0]["date"]
today_price = prices[0]["adj_close"]
today_date = datetime.date.fromisoformat(today_str)
print(f"Oggi (ultimo dato): {today_str} = {today_price}\n")

def find_ref_date_new(prices_desc, target_date):
    candidates = [p for p in prices_desc if p["date"] >= target_date.isoformat()]
    if not candidates: return None
    return min(candidates, key=lambda p: p["date"])

print("=== METODOLOGIA VECCHIA (indici fissi a giorni di trading: 5/21/127/253) ===")
old_indices = {"5 giorni":5, "1 mese":21, "6 mesi":127, "12 mesi":253}
old_results = {}
for label, idx in old_indices.items():
    if len(prices) > idx:
        p = prices[idx]
        chg = round((today_price/p["adj_close"]-1)*100, 2)
        old_results[label] = chg
        print(f"{label}: riferimento {p['date']} = {p['adj_close']} | var = {chg}%")

print("\n=== METODOLOGIA NUOVA (calendario +1gg, snap a trading day, verificata con Yahoo) ===")
new_results = {}
# 5 giorni: 4 posizioni indietro (confermato ieri)
p4 = prices[4]
chg5new = round((today_price/p4["adj_close"]-1)*100, 2)
new_results["5 giorni"] = chg5new
print(f"5 giorni: riferimento {p4['date']} = {p4['adj_close']} | var = {chg5new}%")

for months, label in [(1,"1 mese"), (6,"6 mesi"), (12,"12 mesi")]:
    target = today_date - relativedelta(months=months)
    target_plus1 = target + datetime.timedelta(days=1)
    ref = find_ref_date_new(prices, target_plus1)
    if ref:
        chg = round((today_price/ref["adj_close"]-1)*100, 2)
        new_results[label] = chg
        print(f"{label}: calendario {target.isoformat()} +1gg={target_plus1.isoformat()} -> riferimento reale {ref['date']} = {ref['adj_close']} | var = {chg}%")

print("\n=== DIFFERENZA (nuova - vecchia) ===")
for label in old_results:
    diff = round(new_results[label] - old_results[label], 2)
    print(f"{label}: vecchia={old_results[label]}% | nuova={new_results[label]}% | differenza={diff} punti percentuali")
