# FinTrust Alert Financial Rule Engine

半導體產業專用的官方財報自動抓取、持久化、財務指標計算、子產業規則分析與前端快照服務。

## 正常運作模式

```text
Cloud Scheduler
  → 管理端 refresh endpoint
  → TWSE 最新快照＋MOPS 3–5 年 iXBRL
  → 財務科目正規化
  → Firestore／SQLite 寫入 filings 與 facts
  → 計算 calculated metrics
  → 載入半導體共通＋子產業規則
  → 儲存 analysis run 與 rule results
  → 更新 latest frontend snapshot
  → 前端只讀取已完成快照
```

一般使用者不會在瀏覽器等待五年財報下載；前端呼叫：

```text
GET /api/v1/financial/companies/{ticker}/analysis/latest
```

管理端或 Cloud Scheduler 才會觸發：

```text
POST /api/v1/financial/admin/companies/{ticker}/refresh
```

## 已完成

### 官方資料取得

- TWSE OpenAPI：最新綜合損益表、資產負債表與月營收
- MOPS Inline XBRL：第 4 季／年度合併財報，近 3–5 年
- 使用 Arelle 解析 taxonomy、facts、labels、contexts、期間與單位
- 依 current-year context 選值，排除同一文件中的前期比較數
- 原始 iXBRL 24 小時快取；無法可靠解析時保留 missing／error，不以零補值

### 指標與規則

共同指標包含：

- 營收與年增率
- 毛利率、營業利益率、淨利率
- 存貨與存貨年增率
- 營業現金流、現金轉換比、自由現金流
- 資本支出強度、研發強度
- 負債比、流動比率

規則分成：

- `semiconductor_historical_rules.json`：半導體共通規則
- `foundry_historical_rules.json`：晶圓代工，強調資本支出、自由現金流與毛利率
- `ic_design_historical_rules.json`：IC 設計，強調研發、營收、存貨與現金轉換
- `packaging_testing_historical_rules.json`：封裝測試，強調存貨、現金流與負債同步變化

每個規則結果可輸出：

- 實際值
- 公式與邏輯式
- 門檻
- 證據年度
- 嚴重程度
- 解釋文字
- 規則範圍與版本

### 持久化資料

本機測試預設使用 SQLite；Cloud Run 設定為 Firestore。

持久化內容：

- `financial_filings`
- `normalized_financial_facts`
- `calculated_metrics`
- `analysis_runs`
- `rule_results`
- `latest_analysis_snapshots`

Cloud Run 不使用容器 `/tmp` 保存正式資料；`/tmp` 僅保留 iXBRL 快取。正式分析結果寫入 Firestore。

## API

### 公開讀取

```text
GET /api/v1/financial/health
GET /api/v1/financial/companies
GET /api/v1/financial/rules
GET /api/v1/financial/companies/2330/analysis/latest
GET /api/v1/financial/companies/2330/metrics
GET /api/v1/financial/companies/2330/analysis-runs
```

### 即時計算／除錯

```text
GET /api/v1/financial/statements/2330/analyze
GET /api/v1/financial/statements/2330/history?years=5
```

### 管理端 ingestion

須提供 `X-Ingestion-Token`：

```text
POST /api/v1/financial/admin/companies/2330/refresh?years=5&trigger=demo
POST /api/v1/financial/admin/refresh-all?years=5&trigger=manual
```

在 production 若未設定 `INGESTION_API_TOKEN`，管理端 endpoint 會拒絕執行。

## 本機執行

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -q
```

Windows PowerShell：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -q
```

本機預設：

```text
DATASTORE_BACKEND=sqlite
FINANCIAL_DATABASE_PATH=./data/financial_pipeline.sqlite3
```

## Cloud Run＋Firestore 部署

在 Google Cloud Shell：

```bash
git clone --branch feature/financial-statement-ai-mvp --single-branch https://github.com/UnaLu027/fintrust-alert.git
cd fintrust-alert/backend
bash deploy-cloud-run.sh
```

部署腳本會：

1. 啟用 Cloud Run、Cloud Build、Artifact Registry、Firestore、Cloud Scheduler API。
2. 建立 Firestore `(default)` 資料庫。
3. 建立 Cloud Run runtime service account 並授予 Datastore User。
4. 產生 ingestion token，寫入未追蹤的 `cloudrun.env.yaml`。
5. 以 Firestore 模式部署 FastAPI。

部署完成後建立排程：

```bash
bash setup-cloud-scheduler.sh https://你的-cloud-run-url.run.app
```

排程會在 Asia/Taipei 每天 06:10–06:40 分批更新：

- 2330 台積電
- 2303 聯電
- 2454 聯發科
- 3711 日月光投控

請求採 OIDC service account 並附加 `X-Ingestion-Token`，四家公司錯開執行，降低 MOPS 請求壓力。

## Firebase Hosting 前端

取得 Cloud Run URL 後，在 repo 根目錄：

```bash
bash scripts/deploy-firebase-hosting.sh https://你的-cloud-run-url.run.app
```

前端會設定：

```text
VITE_FINANCIAL_API_BASE_URL=https://你的-cloud-run-url.run.app
```

正式前端預計位於：

```text
https://fintrust-alert.web.app
```

## Demo 建議

1. 在 `/docs` 執行 `POST /admin/companies/2330/refresh`。
2. 查看 Cloud Run logs 中的 `twse_fetch`、`mops_fetch`、`frontend_transform`、`persist`。
3. 查詢 `/companies/2330/metrics` 與 `/analysis-runs`。
4. 查詢 `/companies/2330/analysis/latest`。
5. 開啟前端，確認呈現同一個 `analysis_run_id`。

Meeting 中的手動 refresh 只是模擬 Cloud Scheduler；正式使用流程不依賴一般使用者手動觸發。

## 限制

- 第一版歷史層只使用年度 Q4 合併財報，避免將 Q2／Q3 累計值誤當單季。
- 公司自訂 taxonomy concept 可能需要逐公司補充 alias。
- 子產業規則已拆分，但門檻仍是版本化 MVP 參數，後續需以同子產業中位數與 MAD 校準。
- 尚未完成財報重編版本追蹤、季度累計轉單季、應收帳款週轉與固定資產週轉分析。
- 規則結果只提供財務趨勢與可信度風險提示，不構成投資建議。
