import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

ANOMALIES = [
    # BR
    ("001062148","BR"), ("002278082","BR"), ("009915016","BR"), ("017250539","BR"),
    ("094124352","BR"), ("094124453","BR"), ("094426466","BR"), ("626591203","BR"),
    # SEHK
    ("901","SEHK"), ("2066","SEHK"), ("2627","SEHK"),
    # TSE
    ("8303","TSE"), ("581A","TSE"),
    # LSE
    ("UU.","LSE"),
]

print(f"{'Exchange':<8} {'Ticker':<15} {'Company':<40} {'Yahoo':<20} {'ISIN'}")
print("-" * 100)

for ticker, exchange in ANOMALIES:
    r = requests.get(SUPABASE_URL + "/rest/v1/stocks", headers=headers_r,
        params={"select": "ticker,exchange,company,yahoo_ticker,isin",
                "ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"})
    rows = r.json()
    if isinstance(rows, list) and rows:
        s = rows[0]
        print(f"{exchange:<8} {ticker:<15} {(s.get('company') or 'N/A'):<40} {(s.get('yahoo_ticker') or 'N/A'):<20} {s.get('isin') or 'N/A'}")
    else:
        print(f"{exchange:<8} {ticker:<15} {'NOT FOUND':<40}")
