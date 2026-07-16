import os, requests, csv, io
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}

# Prima lista i bucket disponibili
r0 = requests.get(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers_r)
print("Bucket disponibili:", r0.status_code, r0.text[:500])

# Prova endpoint autenticato diretto per il file
for bucket_name in ["tikr-uploads", "tikr_uploads", "uploads"]:
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/tikr_na_latest.csv"
    r = requests.get(url, headers=headers_r)
    print(f"\nTentativo bucket '{bucket_name}': status {r.status_code}")
    if r.status_code == 200:
        print("TROVATO! Primi 500 caratteri:")
        print(r.text[:500])
        break
