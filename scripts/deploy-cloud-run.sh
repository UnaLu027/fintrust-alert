#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="fintrust-alert"
REGION="asia-east1"
SERVICE="fintrust-alert-api"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v gcloud >/dev/null 2>&1 || {
  echo "找不到 gcloud。請改在 Google Cloud Shell 執行此腳本。" >&2
  exit 1
}

cd "${REPO_ROOT}/backend"

gcloud config set project "${PROJECT_ID}"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

if [[ ! -f cloudrun.env.yaml ]]; then
  cp cloudrun.env.yaml.example cloudrun.env.yaml
  echo "已由範本建立 backend/cloudrun.env.yaml。"
fi

gcloud run deploy "${SERVICE}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --timeout 300 \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 3 \
  --env-vars-file cloudrun.env.yaml

SERVICE_URL="$(gcloud run services describe "${SERVICE}" --region "${REGION}" --format='value(status.url)')"

echo
echo "Cloud Run 部署完成：${SERVICE_URL}"
echo "請先開啟 ${SERVICE_URL}/api/v1/financial/health 驗證，再執行："
echo "bash scripts/deploy-firebase-hosting.sh ${SERVICE_URL}"
