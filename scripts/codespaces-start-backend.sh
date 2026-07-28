#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

if [[ ! -x backend/.venv/bin/python ]]; then
  echo "找不到 backend/.venv，正在建立並安裝依賴。"
  python -m venv backend/.venv
  source backend/.venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r backend/requirements-dev.txt
else
  source backend/.venv/bin/activate
fi

mkdir -p backend/data/mops_ixbrl_cache

export APP_ENV="development"
export DATASTORE_BACKEND="sqlite"
export FINANCIAL_DATABASE_PATH="${REPO_ROOT}/backend/data/financial_pipeline.sqlite3"
export MOPS_XBRL_CACHE_DIR="${REPO_ROOT}/backend/data/mops_ixbrl_cache"
export MOPS_XBRL_CACHE_TTL_HOURS="24"
export LOG_LEVEL="INFO"

if [[ -n "${CODESPACE_NAME:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
  API_URL="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  FRONTEND_URL="https://${CODESPACE_NAME}-5173.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  export CORS_ALLOW_ORIGINS="${FRONTEND_URL},http://localhost:5173,http://127.0.0.1:5173"

  if command -v gh >/dev/null 2>&1; then
    gh codespace ports visibility 8000:public -c "${CODESPACE_NAME}" >/dev/null 2>&1 || true
  fi

  echo "FastAPI Docs：${API_URL}/docs"
  echo "Health：${API_URL}/api/v1/financial/health"
  echo "若外部無法開啟，請到 PORTS 面板將 8000 Visibility 改為 Public。"
else
  export CORS_ALLOW_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
  echo "FastAPI Docs：http://localhost:8000/docs"
fi

echo "SQLite：${FINANCIAL_DATABASE_PATH}"
echo "啟動 FinTrust FastAPI；請保持此 Terminal 開啟。"

cd backend
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
