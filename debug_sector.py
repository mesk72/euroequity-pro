import os, requests
SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
headers_r = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY}
headers_count = {**headers_r, "Prefer": "count=exact"}

sector = "Information Technology"

# Fonte 1 e 2: SectorScreenUS + pagina Sectors, entrambe ora US+TSX, in_universe=true
r1 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","exchange":"in.(US,TSX)","sector":f"eq.{sector}","in_universe":"eq.true"})
count_na = r1.headers.get("content-range","").split("/")[-1]
print(f"SectorScreenUS + pagina Sectors (US+TSX, in_universe=true): {count_na}")

# Fonte 3: Sector Comparison popup (mio endpoint sector-averages) - stesso filtro
print(f"Sector Comparison popup (stessa query): {count_na} (usa identica logica)")

# Per confronto: solo US (il "373" originale)
r2 = requests.get(f"{SUPABASE_URL}/rest/v1/stocks", headers=headers_count,
    params={"select":"ticker","exchange":"eq.US","sector":f"eq.{sector}","in_universe":"eq.true"})
count_us_only = r2.headers.get("content-range","").split("/")[-1]
print(f"\nPer riferimento, solo US (senza TSX): {count_us_only}")
