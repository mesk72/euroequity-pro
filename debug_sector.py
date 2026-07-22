import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_up = {**headers_r, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}

# Prendo pochi titoli reali US con value_score e growth_score gia' presenti
r = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,exchange,value_score,growth_score","exchange":"eq.US",
             "value_score":"not.is.null","growth_score":"not.is.null","limit":"5"})
sample = r.json()
print("Campione:", sample)

test_updates = [{"ticker": d["ticker"], "exchange": d["exchange"], "combined_rank": 50} for d in sample]
print("\nTest payload:", test_updates)

r2 = requests.post(f"{SUPABASE_URL}/rest/v1/fundamentals?on_conflict=ticker,exchange", headers=headers_up, json=test_updates)
print(f"\nRisultato POST: HTTP {r2.status_code}")
print("Corpo risposta:", r2.text[:1000])

# Verifica se ha davvero scritto
r3 = requests.get(f"{SUPABASE_URL}/rest/v1/fundamentals", headers=headers_r,
    params={"select":"ticker,combined_rank","ticker":f"eq.{sample[0]['ticker']}","exchange":"eq.US"})
print("\nVerifica dopo scrittura:", r3.json())
