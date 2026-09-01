#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}/backend"

bash deploy-cloud-run.sh
SERVICE_URL="$(gcloud run services describe fintrust-alert-api --region asia-east1 --format='value(status.url)')"

echo
echo "後端部署完成：${SERVICE_URL}"
echo "建立自動排程："
echo "cd ${REPO_ROOT}/backend && bash setup-cloud-scheduler.sh ${SERVICE_URL}"
echo "部署前端："
echo "cd ${REPO_ROOT} && bash scripts/deploy-firebase-hosting.sh ${SERVICE_URL}"
