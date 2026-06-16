import requests, os, yfinance as yf
from datetime import datetime, date, timedelta

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
headers_up = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}",
              "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}

INDICES = [
    {"ticker": "^FTSEMIB", "name": "FTSE MIB", "exchange": "MIL", "country": "IT"},
    {"ticker": "^GDAXI", "name": "DAX", "exchange": "XETRA", "country": "DE"},
    {"ticker": "^FCHI", "name": "CAC 40", "exchange": "PA", "country": "FR"},
    {"ticker": "^FTSE", "name": "FTSE 100", "exchange": "LSE", "country": "GB"},
    {"ticker": "^AEX", "name": "AEX", "exchange": "AS", "country": "NL"},
    {"ticker": "^IBEX", "name": "IBEX 35", "exchange": "MC", "country": "ES"},
    {"ticker": "^SSMI", "name": "SMI", "exchange": "SWX", "country": "CH"},
    {"ticker": "^OMX", "name": "OMX Stockholm", "exchange": "OM", "country": "SE"},
    {"ticker": "^OBX", "name": "OBX", "exchange": "OB", "country": "NO"},
    {"ticker": "^OMXC25", "name": "OMX Copenhagen","exchange": "CPSE", "country": "DK"},
    {"ticker": "^OMXH25", "name": "OMX Helsinki", "exchange": "HE", "country": "FI"},
    {"ticker": "^BFX", "name": "BEL 20", "exchange": "BR", "country": "BE"},
    {"ticker": "^PSI20", "name": "PSI 20", "exchange": "LS", "country": "PT"},
    {"ticker": "^ATX", "name": "ATX", "exchange": "VI", "country": "AT"},
    {"ticker": "^ISEQ", "name": "ISEQ", "exchange": "IR", "country": "IE"},
    {"ticker": "^STOXX50E","name": "EURO STOXX 50", "exchange": "EZ", "country": "EU"},
    {"ticker": "^STOXX", "name": "STOXX 600", "exchange": "EZ", "country": "EU"},
]

today = date.today().isoformat()
start_ytd = f"{date.today().year}-01-01"
start_5d = (date.today() - timedelta(days=7)).isoformat()
ok = fail = 0

for idx in INDICES:
    try:
        hist = yf.download(idx["ticker"], start=start_5d, progress=False, auto_adjust=True)
        if hist.empty or len(hist) < 2:
            print(f"❌ {idx['name']}: no data")
            fail += 1
            continue

        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        change1d = (price - prev) / prev * 100

        hist_ytd = yf.download(idx["ticker"], start=start_ytd, progress=False, auto_adjust=True)
        ytd = None
        if not hist_ytd.empty:
            price_jan1 = float(hist_ytd["Close"].iloc[0])
            ytd = (price - price_jan1) / price_jan1 * 100

        record = {
            "ticker": idx["ticker"],
            "name": idx["name"],
            "exchange": idx["exchange"],
            "country": idx["country"],
            "price": round(price, 2),
            "change1d": round(change1d, 2),
            "ytd": round(ytd, 2) if ytd is not None else None,
            "date": today,
        }

        r = requests.post(SUPABASE_URL+"/rest/v1/indices", headers=headers_up, json=record)
        if r.status_code in [200, 201]:
            ok += 1
            print(f"✅ {idx['name']}: {price:.0f} ({change1d:+.2f}%)")
        else:
            fail += 1
            print(f"❌ {idx['name']}: {r.status_code}")

    except Exception as e:
        fail += 1
        print(f"⚠️ {idx['name']}: {e}")

print(f"\nCompletato: OK={ok} Fail={fail}")
