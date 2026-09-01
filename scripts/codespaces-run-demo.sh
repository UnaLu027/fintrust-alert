#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TICKER="${1:-2330}"
YEARS="${2:-3}"
END_YEAR="${3:-2024}"
SOURCE_MODE="${4:-official}"
API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"

if [[ ! "${TICKER}" =~ ^(2330|2303|2454|3711)$ ]]; then
  echo "支援代號：2330、2303、2454、3711" >&2
  exit 2
fi
if [[ ! "${YEARS}" =~ ^[3-5]$ ]]; then
  echo "YEARS 必須是 3、4 或 5。" >&2
  exit 2
fi
if [[ "${SOURCE_MODE}" != "official" && "${SOURCE_MODE}" != "demo_fixture" ]]; then
  echo "SOURCE_MODE 必須是 official 或 demo_fixture。" >&2
  exit 2
fi

mkdir -p "${REPO_ROOT}/backend/data/demo-output"
RESPONSE_FILE="${REPO_ROOT}/backend/data/demo-output/refresh-${TICKER}-${SOURCE_MODE}.json"
SNAPSHOT_FILE="${REPO_ROOT}/backend/data/demo-output/snapshot-${TICKER}.json"

printf '等待後端啟動'
for _ in $(seq 1 60); do
  if curl --silent --fail "${API_BASE_URL}/api/v1/financial/health" >/dev/null 2>&1; then
    echo " ready"
    break
  fi
  printf '.'
  sleep 1
done

if ! curl --silent --fail "${API_BASE_URL}/api/v1/financial/health" >/dev/null 2>&1; then
  echo
  echo "後端尚未啟動。請先在另一個 Terminal 執行：" >&2
  echo "  bash scripts/codespaces-start-backend.sh" >&2
  exit 1
fi

URL="${API_BASE_URL}/api/v1/financial/admin/companies/${TICKER}/refresh?years=${YEARS}&end_year=${END_YEAR}&trigger=demo&source_mode=${SOURCE_MODE}"

echo "執行 Demo pipeline"
echo "  ticker=${TICKER} years=${YEARS} end_year=${END_YEAR} source_mode=${SOURCE_MODE}"
if [[ "${SOURCE_MODE}" == "demo_fixture" ]]; then
  echo "  注意：本次使用明確標示的合成 fixture，只驗證技術流程，不代表真實公司財報。"
fi

HTTP_CODE="$(curl --silent --show-error \
  --output "${RESPONSE_FILE}" \
  --write-out '%{http_code}' \
  --request POST \
  "${URL}")"

if [[ "${HTTP_CODE}" != "200" ]]; then
  echo "Pipeline 執行失敗，HTTP ${HTTP_CODE}" >&2
  python -m json.tool "${RESPONSE_FILE}" 2>/dev/null || cat "${RESPONSE_FILE}"
  if [[ "${SOURCE_MODE}" == "official" ]]; then
    echo
    echo "外部官方來源暫時不可用時，可改跑明確標示的流程備援：" >&2
    echo "  bash scripts/codespaces-run-demo.sh ${TICKER} ${YEARS} ${END_YEAR} demo_fixture" >&2
  fi
  exit 1
fi

python -m json.tool "${RESPONSE_FILE}" | sed -n '1,120p'

curl --silent --show-error --fail \
  "${API_BASE_URL}/api/v1/financial/companies/${TICKER}/analysis/latest" \
  > "${SNAPSHOT_FILE}"

echo
echo "資料庫寫入與最新 snapshot 檢查"
cd "${REPO_ROOT}/backend"
source .venv/bin/activate
python scripts/inspect_demo_database.py --ticker "${TICKER}"

echo
echo "輸出檔案："
echo "  ${RESPONSE_FILE}"
echo "  ${SNAPSHOT_FILE}"

if [[ -n "${CODESPACE_NAME:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
  PUBLIC_URL="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  echo
  echo "FastAPI Docs：${PUBLIC_URL}/docs"
  echo "Latest snapshot：${PUBLIC_URL}/api/v1/financial/companies/${TICKER}/analysis/latest"
fi
