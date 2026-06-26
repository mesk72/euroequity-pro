#!/bin/bash
# ============================================================
# FORWARDALPHA — Setup Cloud Scheduler
# Esegui UNA VOLTA dopo il deploy Cloud Run
# Prerequisiti:
#   gcloud auth login
#   gcloud config set project YOUR_PROJECT_ID
# ============================================================

PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west1"
SERVICE_URL=$(gcloud run services describe forwardalpha-runner --region=$REGION --format='value(status.url)')
SECRET=$(gcloud secrets versions access latest --secret="CLOUD_SCHEDULER_SECRET")

echo "Project: $PROJECT_ID"
echo "Service URL: $SERVICE_URL"
echo "Setting up Cloud Scheduler jobs..."

# Crea service account per Cloud Scheduler
gcloud iam service-accounts create forwardalpha-scheduler \
    --display-name="ForwardAlpha Scheduler" 2>/dev/null || true

SA="forwardalpha-scheduler@$PROJECT_ID.iam.gserviceaccount.com"

# Permesso di invocare Cloud Run
gcloud run services add-iam-policy-binding forwardalpha-runner \
    --region=$REGION \
    --member="serviceAccount:$SA" \
    --role="roles/run.invoker"

# ── DAILY JOBS ────────────────────────────────────────────

# Daily APAC — 09:00 UTC (11:00 CET) lun-ven
gcloud scheduler jobs create http daily-apac \
    --location=$REGION \
    --schedule="0 9 * * 1-5" \
    --uri="$SERVICE_URL/daily-apac" \
    --http-method=POST \
    --oidc-service-account-email=$SA \
    --headers="Authorization=Bearer $SECRET" \
    --attempt-deadline=3600s \
    --time-zone="Europe/Rome" \
    --description="ForwardAlpha Daily APAC load" 2>/dev/null || \
gcloud scheduler jobs update http daily-apac \
    --location=$REGION \
    --schedule="0 9 * * 1-5" \
    --uri="$SERVICE_URL/daily-apac" \
    --http-method=POST

# Daily EU — 19:00 UTC (21:00 CET) lun-ven
gcloud scheduler jobs create http daily-eu \
    --location=$REGION \
    --schedule="0 19 * * 1-5" \
    --uri="$SERVICE_URL/daily-eu" \
    --http-method=POST \
    --oidc-service-account-email=$SA \
    --headers="Authorization=Bearer $SECRET" \
    --attempt-deadline=3600s \
    --time-zone="Europe/Rome" \
    --description="ForwardAlpha Daily EU load" 2>/dev/null || \
gcloud scheduler jobs update http daily-eu \
    --location=$REGION \
    --schedule="0 19 * * 1-5" \
    --uri="$SERVICE_URL/daily-eu" \
    --http-method=POST

# Daily US — 23:00 UTC (01:00 CET) lun-ven
gcloud scheduler jobs create http daily-us \
    --location=$REGION \
    --schedule="0 23 * * 1-5" \
    --uri="$SERVICE_URL/daily-us" \
    --http-method=POST \
    --oidc-service-account-email=$SA \
    --headers="Authorization=Bearer $SECRET" \
    --attempt-deadline=3600s \
    --time-zone="Europe/Rome" \
    --description="ForwardAlpha Daily US+CA load" 2>/dev/null || \
gcloud scheduler jobs update http daily-us \
    --location=$REGION \
    --schedule="0 23 * * 1-5" \
    --uri="$SERVICE_URL/daily-us" \
    --http-method=POST

# ── WEEKLY JOBS ───────────────────────────────────────────

# Weekly EU — domenica 07:00 UTC (09:00 CET)
gcloud scheduler jobs create http weekly-eu \
    --location=$REGION \
    --schedule="0 7 * * 0" \
    --uri="$SERVICE_URL/weekly-eu" \
    --http-method=POST \
    --oidc-service-account-email=$SA \
    --headers="Authorization=Bearer $SECRET" \
    --attempt-deadline=3600s \
    --description="ForwardAlpha Weekly EU" 2>/dev/null || true

# Weekly US — domenica 07:00 UTC
gcloud scheduler jobs create http weekly-us \
    --location=$REGION \
    --schedule="0 7 * * 0" \
    --uri="$SERVICE_URL/weekly-us" \
    --http-method=POST \
    --oidc-service-account-email=$SA \
    --headers="Authorization=Bearer $SECRET" \
    --attempt-deadline=3600s \
    --description="ForwardAlpha Weekly US+CA" 2>/dev/null || true

# Weekly APAC — domenica 08:00 UTC (10:00 CET)
gcloud scheduler jobs create http weekly-apac \
    --location=$REGION \
    --schedule="0 8 * * 0" \
    --uri="$SERVICE_URL/weekly-apac" \
    --http-method=POST \
    --oidc-service-account-email=$SA \
    --headers="Authorization=Bearer $SECRET" \
    --attempt-deadline=3600s \
    --description="ForwardAlpha Weekly APAC" 2>/dev/null || true

# ── NEWS CACHE — ogni 3 ore ───────────────────────────────
gcloud scheduler jobs create http fetch-news \
    --location=$REGION \
    --schedule="0 */3 * * *" \
    --uri="$SERVICE_URL/fetch-news" \
    --http-method=POST \
    --oidc-service-account-email=$SA \
    --headers="Authorization=Bearer $SECRET" \
    --attempt-deadline=2700s \
    --description="ForwardAlpha Fetch News Cache" 2>/dev/null || true

echo ""
echo "✅ Cloud Scheduler configurato!"
echo "Jobs creati:"
gcloud scheduler jobs list --location=$REGION
