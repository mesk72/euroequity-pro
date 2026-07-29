import os, requests, yfinance as yf
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

print("=== TSX .UN: come viene mappato il ticker per Yahoo? ===")
rs = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,yahoo_ticker","ticker":"eq.CAR.UN","exchange":"eq.TSX"})
print("stocks:", rs.json())
for ytk in ["CAR-UN.TO", "CAR.UN.TO", "CAR-UN.V"]:
    try:
        df = yf.download(ytk, period="5d", progress=False)
        print(f"  {ytk}: {'DATI OK' if not df.empty else 'vuoto'}")
    except Exception as e:
        print(f"  {ytk}: errore {e}")

print("\n=== KRX A0xxxxx: come viene mappato? ===")
rs2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_r,
    params={"select":"ticker,exchange,yahoo_ticker","ticker":"eq.A000250","exchange":"eq.KRX"})
print("stocks:", rs2.json())
for ytk in ["000250.KS", "A000250.KS", "000250.KQ"]:
    try:
        df = yf.download(ytk, period="5d", progress=False)
        print(f"  {ytk}: {'DATI OK' if not df.empty else 'vuoto'}")
    except Exception as e:
        print(f"  {ytk}: errore {e}")
