#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-fintrust-alert}"
REGION="${REGION:-asia-east1}"
SCHEDULER_SA_NAME="${SCHEDULER_SA_NAME:-fintrust-alert-scheduler}"
SCHEDULER_SA_EMAIL="${SCHEDULER_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
TOKEN_FILE="${TOKEN_FILE:-.ingestion-token}"
RUN_INITIAL_REFRESH="${RUN_INITIAL_REFRESH:-true}"

if [[ $# -ne 1 ]]; then
  echo "用法：bash setup-cloud-scheduler.sh <CLOUD_RUN_URL>" >&2
  exit 1
fi

SERVICE_URL="${1%/}"
if [[ ! "${SERVICE_URL}" =~ ^https://.+\.run\.app$ ]]; then
  echo "Cloud Run URL 格式不正確：${SERVICE_URL}" >&2
  exit 1
fi
if [[ ! -f "${TOKEN_FILE}" ]]; then
  echo "找不到 ${TOKEN_FILE}。請先執行 bash deploy-cloud-run.sh。" >&2
  exit 1
fi

INGESTION_TOKEN="$(tr -d '\r\n' < "${TOKEN_FILE}")"
gcloud config set project "${PROJECT_ID}"
gcloud services enable cloudscheduler.googleapis.com iam.googleapis.com

if ! gcloud iam service-accounts describe "${SCHEDULER_SA_EMAIL}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SCHEDULER_SA_NAME}" \
    --display-name="FinTrust Alert Cloud Scheduler"
fi

gcloud run services add-iam-policy-binding fintrust-alert-api \
  --region "${REGION}" \
  --member="serviceAccount:${SCHEDULER_SA_EMAIL}" \
  --role="roles/run.invoker" >/dev/null

create_or_update_job() {
  local ticker="$1"
  local schedule="$2"
  local job="fintrust-refresh-${ticker}"
  local uri="${SERVICE_URL}/api/v1/financial/admin/companies/${ticker}/refresh?years=5&trigger=scheduler"

  if gcloud scheduler jobs describe "${job}" --location "${REGION}" >/dev/null 2>&1; then
    gcloud scheduler jobs update http "${job}" \
      --location "${REGION}" \
      --schedule "${schedule}" \
      --time-zone "Asia/Taipei" \
      --uri "${uri}" \
      --http-method POST \
      --headers "X-Ingestion-Token=${INGESTION_TOKEN},Content-Type=application/json" \
      --message-body '{}' \
      --oidc-service-account-email "${SCHEDULER_SA_EMAIL}" \
      --oidc-token-audience "${SERVICE_URL}" \
      --attempt-deadline 1800s
  else
    gcloud scheduler jobs create http "${job}" \
      --location "${REGION}" \
      --schedule "${schedule}" \
      --time-zone "Asia/Taipei" \
      --uri "${uri}" \
      --http-method POST \
      --headers "X-Ingestion-Token=${INGESTION_TOKEN},Content-Type=application/json" \
      --message-body '{}' \
      --oidc-service-account-email "${SCHEDULER_SA_EMAIL}" \
      --oidc-token-audience "${SERVICE_URL}" \
      --attempt-deadline 1800s
  fi
}

create_or_update_job "2330" "10 6 * * *"
create_or_update_job "2303" "20 6 * * *"
create_or_update_job "2454" "30 6 * * *"
create_or_update_job "3711" "40 6 * * *"

echo
echo "Cloud Scheduler 已建立：每天 Asia/Taipei 06:10–06:40 依序更新四家公司。"

if [[ "${RUN_INITIAL_REFRESH}" == "true" ]]; then
  echo "啟動首次資料建立；Scheduler jobs 會在背景依序送出請求。"
  for ticker in 2330 2303 2454 3711; do
    gcloud scheduler jobs run "fintrust-refresh-${ticker}" --location "${REGION}"
  done
  echo "首次分析執行中。可到 Cloud Run Logs 或 Firestore 查看進度。"
else
  echo "略過首次 refresh。可手動執行：gcloud scheduler jobs run fintrust-refresh-2330 --location ${REGION}"
fi
