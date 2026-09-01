#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-fintrust-alert}"
REGION="${REGION:-asia-east1}"
SERVICE="${SERVICE:-fintrust-alert-api}"
RUNTIME_SA_NAME="${RUNTIME_SA_NAME:-fintrust-alert-runtime}"
RUNTIME_SA_EMAIL="${RUNTIME_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
TOKEN_FILE="${TOKEN_FILE:-.ingestion-token}"

command -v gcloud >/dev/null 2>&1 || {
  echo "找不到 gcloud。請在 Google Cloud Shell 執行此腳本。" >&2
  exit 1
}

echo "[1/7] 使用 Google Cloud 專案：${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}"

echo "[2/7] 啟用 Cloud Run、Cloud Build、Artifact Registry、Firestore、Scheduler API"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  cloudscheduler.googleapis.com \
  iam.googleapis.com

echo "[3/7] 確認 Firestore (default) 資料庫"
if ! gcloud firestore databases describe --database='(default)' >/dev/null 2>&1; then
  gcloud firestore databases create \
    --database='(default)' \
    --location="${REGION}" \
    --type=firestore-native
else
  echo "Firestore (default) 已存在。"
fi

echo "[4/7] 建立 Cloud Run 執行服務帳戶"
if ! gcloud iam service-accounts describe "${RUNTIME_SA_EMAIL}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${RUNTIME_SA_NAME}" \
    --display-name="FinTrust Alert Cloud Run runtime"
fi

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA_EMAIL}" \
  --role="roles/datastore.user" \
  --condition=None >/dev/null

echo "[5/7] 建立 ingestion token 與 Cloud Run 環境檔"
if [[ ! -f "${TOKEN_FILE}" ]]; then
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32 > "${TOKEN_FILE}"
  else
    python3 -c 'import secrets; print(secrets.token_hex(32))' > "${TOKEN_FILE}"
  fi
  chmod 600 "${TOKEN_FILE}"
fi
INGESTION_TOKEN="$(tr -d '\r\n' < "${TOKEN_FILE}")"
cat > cloudrun.env.yaml <<EOF
APP_ENV: "production"
GOOGLE_CLOUD_PROJECT: "${PROJECT_ID}"
DATASTORE_BACKEND: "firestore"
CORS_ALLOW_ORIGINS: "https://${PROJECT_ID}.web.app,https://${PROJECT_ID}.firebaseapp.com"
INGESTION_API_TOKEN: "${INGESTION_TOKEN}"
MOPS_XBRL_CACHE_DIR: "/tmp/fintrust/mops_ixbrl_cache"
MOPS_XBRL_CACHE_TTL_HOURS: "24"
FINANCIAL_DATABASE_PATH: "/tmp/fintrust/financial_pipeline.sqlite3"
EOF

echo "[6/7] 部署 ${SERVICE} 到 Cloud Run"
gcloud run deploy "${SERVICE}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --service-account "${RUNTIME_SA_EMAIL}" \
  --timeout 900 \
  --memory 2Gi \
  --cpu 1 \
  --concurrency 4 \
  --max-instances 3 \
  --env-vars-file cloudrun.env.yaml

SERVICE_URL="$(gcloud run services describe "${SERVICE}" --region "${REGION}" --format='value(status.url)')"

echo "[7/7] 部署完成"
echo "Cloud Run URL：${SERVICE_URL}"
echo "Health check：${SERVICE_URL}/api/v1/financial/health"
echo "Token 已保存在 backend/${TOKEN_FILE}，請勿提交 GitHub。"
echo "下一步：bash setup-cloud-scheduler.sh ${SERVICE_URL}"
