import os, requests
from datetime import datetime
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_up = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
              "Content-Type": "application/json",
              "Prefer": "resolution=merge-duplicates,return=minimal"}
test_row = [{
    "ticker": "TESTXYZ", "exchange": "US", "region": "americas",
    "company": "Test Co", "yahoo_ticker": "TESTXYZ",
    "title": "Test news title", "link": "https://example.com/test",
    "pub_date": datetime.now().isoformat(), "source": "test",
    "value_score": 50, "growth_score": 50, "best_score": 50,
    "mkt_cap": 100.0,
    "fetched_at": datetime.now().isoformat(),
}]
r = requests.post(SUPABASE_URL + "/rest/v1/news_cache", headers=headers_up, json=test_row)
print(f"HTTP {r.status_code}")
print(r.text[:800])
