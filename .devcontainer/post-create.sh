#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "[1/4] 建立 Python 虛擬環境"
python -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip

echo "[2/4] 安裝 FastAPI、MOPS XBRL 與測試依賴"
pip install -r backend/requirements-dev.txt

echo "[3/4] 安裝前端依賴"
npm ci

echo "[4/4] 準備 Demo 資料目錄與腳本權限"
mkdir -p backend/data/mops_ixbrl_cache
chmod +x scripts/codespaces-start-backend.sh scripts/codespaces-run-demo.sh 2>/dev/null || true

cat <<'EOF'

Codespaces 環境準備完成。

啟動後端：
  bash scripts/codespaces-start-backend.sh

另開一個 Terminal 執行官方資料 Demo：
  bash scripts/codespaces-run-demo.sh 2330 3 2024 official

官方來源暫時無法連線時，才使用明確標示的流程備援資料：
  bash scripts/codespaces-run-demo.sh 2330 3 2024 demo_fixture
EOF
