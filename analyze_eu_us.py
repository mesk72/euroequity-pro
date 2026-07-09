import os, requests
from datetime import datetime, timedelta
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
LEEWAY_KEY   = os.environ.get("LEEWAY_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

LEEWAY_SUFFIX = {"AS":".AS","XETRA":".XETRA","PA":".PA","LSE":".L","SWX":".SW",
    "OM":".ST","OB":".OL","CPSE":".CO","MC":".MC","BR":".BR","GR":".AT",
    "VI":".VI","IR":".IR","LS":".LS","MIL":".MI"}

EXCHANGES = ["LSE","XETRA","PA","OM","SWX","MIL","AS","MC","BR","HE","CPSE","OB","GR","VI","IR","LS"]

to_d = datetime.now().strftime("%Y-%m-%d")
from_d = (datetime.now()-timedelta(days=15)).strftime("%Y-%m-%d")

print("=" * 70)
print(f"{'Exch':<7}{'DB max date (5 sample)':<45}{'Leeway ha 8/7?':<20}")
print("=" * 70)
for exch in EXCHANGES:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
        params={"select":"ticker","in_universe":"eq.true","exchange":f"eq.{exch}","limit":"5"})
    tickers = [s["ticker"] for s in r.json()] if isinstance(r.json(),list) else []
    db_dates = []
    for t in tickers:
        rp = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
            params={"select":"date","ticker":f"eq.{t}","exchange":f"eq.{exch}","order":"date.desc","limit":"1"})
        d = rp.json()
        db_dates.append(d[0]["date"] if isinstance(d,list) and d else "VUOTO")
    # Test diretto Leeway sul primo ticker del campione
    leeway_status = "N/A"
    if tickers:
        t0 = tickers[0]
        lt = t0.rstrip(".") + LEEWAY_SUFFIX.get(exch,"")
        url = f"https://api.leeway.tech/api/v1/public/historicalquotes/{lt}?apitoken={LEEWAY_KEY}&from={from_d}&to={to_d}"
        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data,list) and data:
                    max_d = max(d["date"] for d in data)
                    leeway_status = f"Leeway max={max_d}"
                else:
                    leeway_status = "Leeway: vuoto"
            else:
                leeway_status = f"HTTP {resp.status_code}"
        except Exception as e:
            leeway_status = f"ERR {e}"
    print(f"{exch:<7}{str(db_dates):<45}{leeway_status:<20} (test:{tickers[0] if tickers else '-'})")
