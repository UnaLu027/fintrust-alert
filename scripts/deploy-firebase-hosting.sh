#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="fintrust-alert"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ $# -ne 1 ]]; then
  echo "用法：bash scripts/deploy-firebase-hosting.sh <CLOUD_RUN_URL>" >&2
  exit 1
fi

CLOUD_RUN_URL="${1%/}"
if [[ ! "${CLOUD_RUN_URL}" =~ ^https://.+\.run\.app$ ]]; then
  echo "Cloud Run URL 格式不正確：${CLOUD_RUN_URL}" >&2
  exit 1
fi

cd "${REPO_ROOT}"
printf 'VITE_FINANCIAL_API_BASE_URL=%s\n' "${CLOUD_RUN_URL}" > .env.production.local

npm ci
npm run build
npx firebase-tools deploy --only hosting --project "${PROJECT_ID}"

echo
echo "Firebase Hosting 部署完成："
echo "https://${PROJECT_ID}.web.app"
echo "https://${PROJECT_ID}.firebaseapp.com"
