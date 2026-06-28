# ============================================================
# FORWARDALPHA — UPLOAD INIZIALE SU SUPABASE STORAGE
# Da eseguire UNA VOLTA SOLA da Google Colab
# Dopo questo, tutto gira da GitHub Actions
# ============================================================
# File necessari (da caricare in Colab prima di eseguire):
#   tikr_eu_latest.csv     — TIKR Europa (scaricato da TIKR)
#   tikr_na_latest.csv     — TIKR Nord America US+CA (scaricato da TIKR)
#   fiscal_year_end_eu.csv — Fiscal year end Europa (colonne: ticker, exchange, fiscal_month)
#   fiscal_year_end_na.csv — Fiscal year end Nord America (colonne: ticker, exchange, fiscal_month)
# ============================================================

import requests, io, os
import pandas as pd

SUPABASE_URL = "YOUR_SUPABASE_URL"  # es. https://mlqkisnizgyvvqajdvbh.supabase.co
SERVICE_KEY  = "YOUR_SERVICE_KEY"

headers_auth = {
    "apikey": SERVICE_KEY,
    "Authorization": "Bearer " + SERVICE_KEY,
}

def upload_to_storage(local_path, storage_name):
    """Carica un file su Supabase Storage bucket tikr-uploads"""
    with open(local_path, "rb") as f:
        content = f.read()
    
    # Prima prova DELETE (per sovrascrivere)
    requests.delete(
        f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/{storage_name}",
        headers=headers_auth
    )
    
    # Poi upload
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/tikr-uploads/{storage_name}",
        headers={**headers_auth, "Content-Type": "text/csv"},
        data=content
    )
    if r.status_code in (200, 201):
        print(f"  ✅ {storage_name} caricato ({len(content)//1024} KB)")
    else:
        print(f"  ❌ {storage_name} errore: {r.status_code} {r.text[:100]}")

# ── STEP 1: Carica file TIKR ──────────────────────────────────
print("=== UPLOAD FILE TIKR ===")
upload_to_storage("tikr_eu_latest.csv", "tikr_eu_latest.csv")
upload_to_storage("tikr_na_latest.csv", "tikr_na_latest.csv")

# ── STEP 2: Unifica e carica fiscal_year_end ─────────────────
print("\n=== UPLOAD FISCAL YEAR END ===")

# Leggi i due file fiscal year end
df_eu = pd.read_csv("fiscal_year_end_eu.csv")
df_na = pd.read_csv("fiscal_year_end_na.csv")

# Assicurati che abbiano le colonne giuste: ticker, exchange, fiscal_month
# Se nel tuo file si chiamano diversamente, rinominale qui
# es. df_eu = df_eu.rename(columns={"Ticker": "ticker", "Exchange": "exchange", "FY Month": "fiscal_month"})

print(f"  EU: {len(df_eu)} righe, colonne: {list(df_eu.columns)}")
print(f"  NA: {len(df_na)} righe, colonne: {list(df_na.columns)}")

# Unifica in un file unico
df_all = pd.concat([df_eu, df_na], ignore_index=True)
df_all = df_all[["ticker", "exchange", "fiscal_month"]].drop_duplicates()
print(f"  Totale unificato: {len(df_all)} righe")

# Salva e carica
df_all.to_csv("fiscal_year_end.csv", index=False)
upload_to_storage("fiscal_year_end.csv", "fiscal_year_end.csv")

print("\n=== FATTO ===")
print("Ora puoi lanciare Weekly EU Load e Weekly US Load da GitHub Actions.")
print("Da oggi in poi: carica solo tikr_eu_latest.csv e tikr_na_latest.csv su Supabase Storage")
print("e lancia i weekly da GitHub Actions. Non serve più Colab.")
