#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-fintrust-alert}"
REGION="${REGION:-asia-east1}"
SERVICE="${SERVICE:-fintrust-alert-api}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "找不到 gcloud。請在 Google Cloud Shell 執行此腳本，或先安裝 Google Cloud CLI。" >&2
  exit 1
fi

echo "[1/4] 使用 Google Cloud 專案：${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}"

echo "[2/4] 啟用 Cloud Run、Cloud Build、Artifact Registry API"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

if [[ ! -f cloudrun.env.yaml ]]; then
  echo "[3/4] 由範本建立 cloudrun.env.yaml"
  cp cloudrun.env.yaml.example cloudrun.env.yaml
else
  echo "[3/4] 使用現有 cloudrun.env.yaml"
fi

echo "[4/4] 部署 ${SERVICE} 到 ${REGION}"
gcloud run deploy "${SERVICE}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --timeout 300 \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 3 \
  --env-vars-file cloudrun.env.yaml

echo
echo "部署完成。請複製上方輸出的 Service URL，下一步會填入 .env.production.local。"
