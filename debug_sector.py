import os, requests, yfinance as yf
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

for tk in ["4974", "6961", "8098"]:
    print(f"\n=== {tk}.TSE ===")
    r = requests.get(f"{SUPABASE_URL}/rest/v1/prices_eod", headers=headers_r,
        params={"select":"date,adj_close","ticker":f"eq.{tk}","exchange":"eq.TSE","order":"date.desc","limit":"3"})
    print("DB:", r.json())
    ytk = tk.lstrip("0") + ".T" if tk.isdigit() else tk + ".T"
    try:
        df = yf.download(ytk, period="5d", interval="1d", auto_adjust=True, progress=False)
        print(f"Yahoo ({ytk}):", df["Close"].tail(3).to_dict() if not df.empty else "VUOTO")
    except Exception as e:
        print("Yahoo errore:", e)
