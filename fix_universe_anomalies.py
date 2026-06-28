import os, requests

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
             "Content-Type": "application/json", "Prefer": "return=minimal"}

REMOVE = [
    ("001062148","BR"), ("002278082","BR"), ("009915016","BR"), ("017250539","BR"),
    ("094124352","BR"), ("094124453","BR"), ("094426466","BR"), ("626591203","BR"),
    ("901","SEHK"), ("2066","SEHK"), ("2627","SEHK"),
    ("8303","TSE"), ("581A","TSE"),
]

for ticker, exchange in REMOVE:
    r = requests.patch(
        SUPABASE_URL + "/rest/v1/stocks",
        headers=headers_r,
        params={"ticker": f"eq.{ticker}", "exchange": f"eq.{exchange}"},
        json={"in_universe": False}
    )
    print(f"  {exchange} {ticker}: HTTP {r.status_code} {'OK' if r.status_code in [200,204] else 'FAIL'}")

print("Done.")
