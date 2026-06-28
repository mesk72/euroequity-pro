import pandas as pd
import requests
import io

SUPABASE_URL = "https://mlqkisnizgyvvqajdvbh.supabase.co"
SERVICE_KEY  = "YOUR_SERVICE_KEY"  # sostituisci con la tua chiave

headers_auth = {
    "apikey": SERVICE_KEY,
    "Authorization": "Bearer " + SERVICE_KEY,
}

def upload_to_storage(content_bytes, storage_name):
    requests.delete(
        f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/{storage_name}",
        headers=headers_auth
    )
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/{storage_name}",
        headers={**headers_auth, "Content-Type": "text/csv"},
        data=content_bytes
    )
    kb = len(content_bytes) // 1024
    if r.status_code in (200, 201):
        print(f"  OK {storage_name} ({kb} KB)")
    else:
        print(f"  ERRORE {storage_name}: {r.status_code} {r.text[:150]}")

# ── Mostra colonne di tutti i file ───────────────────────────
print("=== COLONNE FILE ===")
for f in [
    "fiscal_year_end_final.csv",
    "fiscal_year_global.csv",
    "tikr_load_eu_2806 - Foglio1.csv",
    "tikr_load_na_2806 - Foglio1.csv",
]:
    df = pd.read_csv(f, nrows=2)
    print(f"\n{f}:")
    print(f"  {list(df.columns)}")
    print(f"  {df.iloc[0].to_dict()}")

# ── TIKR EU ───────────────────────────────────────────────────
print("\n=== TIKR EU ===")
df_eu = pd.read_csv("tikr_load_eu_2806 - Foglio1.csv")
print(f"  Righe: {len(df_eu)}")
buf = df_eu.to_csv(index=False).encode("utf-8")
upload_to_storage(buf, "tikr_eu_latest.csv")

# ── TIKR NA (solo US — escludi Canada TSX) ───────────────────
print("\n=== TIKR NA (solo US) ===")
df_na = pd.read_csv("tikr_load_na_2806 - Foglio1.csv")
print(f"  Righe totali: {len(df_na)}")
print(f"  Colonna exchange/market: cerca tra {[c for c in df_na.columns if any(k in c.lower() for k in ['exch','market','country','bors'])]}")

# Filtra solo US — escludi Canada
# Adatta il nome colonna dopo aver visto l'output sopra
EXCH_COL = None
for col in df_na.columns:
    if any(k in col.lower() for k in ["exchange", "market", "bors"]):
        EXCH_COL = col
        break

if EXCH_COL:
    print(f"  Uso colonna: {EXCH_COL}")
    print(f"  Valori unici: {df_na[EXCH_COL].unique()[:20]}")
    # Escludi TSX/TSXV canadesi
    df_us = df_na[~df_na[EXCH_COL].str.upper().isin(["TSX","TSXV","TO"])]
    print(f"  Righe US dopo filtro: {len(df_us)}")
else:
    print("  ATTENZIONE: colonna exchange non trovata — carico tutto")
    df_us = df_na

buf = df_us.to_csv(index=False).encode("utf-8")
upload_to_storage(buf, "tikr_na_latest.csv")

# ── FISCAL YEAR END EU ────────────────────────────────────────
print("\n=== FISCAL YEAR END EU ===")
df_fy_eu = pd.read_csv("fiscal_year_end_final.csv")
print(f"  Righe: {len(df_fy_eu)}")
print(f"  Colonne: {list(df_fy_eu.columns)}")

# Rinomina colonne per il formato atteso: ticker, exchange, fiscal_month
# Adatta dopo aver visto le colonne
col_map_eu = {}
for col in df_fy_eu.columns:
    cl = col.lower()
    if "ticker" in cl: col_map_eu[col] = "ticker"
    elif "exchange" in cl or "bors" in cl: col_map_eu[col] = "exchange"
    elif "month" in cl or "mese" in cl or "fiscal" in cl: col_map_eu[col] = "fiscal_month"

df_fy_eu = df_fy_eu.rename(columns=col_map_eu)
df_fy_eu = df_fy_eu[["ticker","exchange","fiscal_month"]].dropna()
print(f"  Dopo pulizia: {len(df_fy_eu)} righe")
buf = df_fy_eu.to_csv(index=False).encode("utf-8")
upload_to_storage(buf, "fiscal_year_end_eu.csv")

# ── FISCAL YEAR END NA (solo US) ─────────────────────────────
print("\n=== FISCAL YEAR END NA (solo US) ===")
df_fy_na = pd.read_csv("fiscal_year_global.csv")
print(f"  Righe: {len(df_fy_na)}")
print(f"  Colonne: {list(df_fy_na.columns)}")

col_map_na = {}
for col in df_fy_na.columns:
    cl = col.lower()
    if "ticker" in cl: col_map_na[col] = "ticker"
    elif "exchange" in cl or "bors" in cl: col_map_na[col] = "exchange"
    elif "month" in cl or "mese" in cl or "fiscal" in cl: col_map_na[col] = "fiscal_month"

df_fy_na = df_fy_na.rename(columns=col_map_na)
df_fy_na = df_fy_na[["ticker","exchange","fiscal_month"]].dropna()

# Filtra solo US — escludi TSX
df_fy_us = df_fy_na[~df_fy_na["exchange"].str.upper().isin(["TSX","TSXV","TO"])]
print(f"  Righe US dopo filtro: {len(df_fy_us)}")
buf = df_fy_us.to_csv(index=False).encode("utf-8")
upload_to_storage(buf, "fiscal_year_end_na.csv")

# ── FISCAL YEAR END UNIFICATO (EU + US) ──────────────────────
print("\n=== FISCAL YEAR END UNIFICATO ===")
df_all = pd.concat([df_fy_eu, df_fy_us], ignore_index=True).drop_duplicates()
print(f"  Totale: {len(df_all)} righe")
buf = df_all.to_csv(index=False).encode("utf-8")
upload_to_storage(buf, "fiscal_year_end.csv")

print("\n=== TUTTO CARICATO ===")
print("Ora lancia Weekly EU Load e Weekly US Load da GitHub Actions.")
