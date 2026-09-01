# Firebase Hosting、Cloud Run、Firestore 與 Cloud Scheduler 串接

本文件對應：

```text
Firebase Project ID: fintrust-alert
Git branch: feature/financial-statement-ai-mvp
Frontend: https://fintrust-alert.web.app
Region: asia-east1
Cloud Run service: fintrust-alert-api
```

## 完整架構

```text
Cloud Scheduler
  → Cloud Run ingestion endpoint
  → TWSE OpenAPI＋MOPS Inline XBRL
  → Firestore：filings／facts／metrics／runs／rules／snapshot
  → Firebase Hosting 前端讀取 latest snapshot
```

前端不直接觸發五年財報下載。正常畫面只呼叫：

```text
GET /api/v1/financial/companies/{ticker}/analysis/latest
```

## 部署前條件

1. Firebase 專案 `fintrust-alert` 已建立。
2. 專案已連結 Cloud Billing。
3. 使用具有專案管理權限的 Google 帳戶開啟 Google Cloud Shell。
4. Draft PR 尚未合併，部署時使用 feature branch。

## 一、取得程式

在 Cloud Shell 執行：

```bash
git clone --branch feature/financial-statement-ai-mvp --single-branch https://github.com/UnaLu027/fintrust-alert.git
cd fintrust-alert/backend
```

若先前已 clone：

```bash
cd ~/fintrust-alert
git checkout feature/financial-statement-ai-mvp
git pull
cd backend
```

## 二、部署 Cloud Run 與 Firestore

```bash
bash deploy-cloud-run.sh
```

腳本會自動：

1. 選擇 `fintrust-alert` 專案。
2. 啟用 Cloud Run、Cloud Build、Artifact Registry、Firestore、Cloud Scheduler 與 IAM API。
3. 若不存在，建立 Firestore `(default)` Native database。
4. 建立 `fintrust-alert-runtime` service account。
5. 授予 runtime service account `roles/datastore.user`。
6. 產生隨機 ingestion token，保存在 `backend/.ingestion-token`。
7. 產生未追蹤的 `backend/cloudrun.env.yaml`。
8. 以 `DATASTORE_BACKEND=firestore` 部署 FastAPI。
9. 設定 900 秒 timeout、2 GiB 記憶體、concurrency 4、最多 3 instances。

完成後記錄 Cloud Run Service URL，例如：

```text
https://fintrust-alert-api-xxxxxxxxxx-de.a.run.app
```

先驗證：

```text
<CLOUD_RUN_URL>/
<CLOUD_RUN_URL>/docs
<CLOUD_RUN_URL>/api/v1/financial/health
```

## 三、建立每日自動更新排程

仍在 `backend/`：

```bash
bash setup-cloud-scheduler.sh <CLOUD_RUN_URL>
```

腳本會建立四個工作，時區均為 `Asia/Taipei`：

```text
06:10  2330 台積電
06:20  2303 聯電
06:30  2454 聯發科
06:40  3711 日月光投控
```

每個工作會呼叫：

```text
POST /api/v1/financial/admin/companies/{ticker}/refresh?years=5&trigger=scheduler
```

安全設定：

- Cloud Scheduler 使用專屬 service account 發送 OIDC token。
- ingestion endpoint 另外驗證 `X-Ingestion-Token`。
- token 不提交 GitHub。

腳本預設會在建立排程後立刻執行四家公司首次 refresh。可到以下位置查看：

```text
Google Cloud Console → Cloud Run → fintrust-alert-api → Logs
Google Cloud Console → Firestore Database → Data
```

Logs 的主要階段：

```text
pipeline_started
twse_fetch
twse_complete
mops_fetch
mops_complete
frontend_transform
persist
pipeline_completed
```

## 四、驗證資料已寫入 Firestore

Firestore 應出現：

```text
financial_filings
normalized_financial_facts
calculated_metrics
analysis_runs
rule_results
latest_analysis_snapshots
```

API 驗收：

```text
<CLOUD_RUN_URL>/api/v1/financial/companies/2330/analysis/latest
<CLOUD_RUN_URL>/api/v1/financial/companies/2330/metrics
<CLOUD_RUN_URL>/api/v1/financial/companies/2330/analysis-runs
```

若 latest endpoint 回傳 404，代表首次 refresh 尚未完成；先查看 Scheduler execution 與 Cloud Run logs。

## 五、部署 Firebase Hosting

回到 repo 根目錄：

```bash
cd ..
bash scripts/deploy-firebase-hosting.sh <CLOUD_RUN_URL>
```

腳本會：

1. 建立 `.env.production.local`。
2. 寫入 `VITE_FINANCIAL_API_BASE_URL`。
3. 執行 `npm ci`。
4. 執行 production build。
5. 部署 Firebase Hosting。

完成後開啟：

```text
https://fintrust-alert.web.app
```

選擇公司後，前端會自動讀取 Firestore 中最新完成的 snapshot；「重新讀取最新快照」只重新查詢資料庫，不會重新下載財報。

## 六、Meeting Demo

### 1. 顯示 refresh 前的資料

```text
GET /api/v1/financial/companies/2330/analysis-runs
```

### 2. 在 `/docs` 觸發管理端 refresh

Endpoint：

```text
POST /api/v1/financial/admin/companies/2330/refresh?years=3&end_year=2024&trigger=demo
```

Header：

```text
X-Ingestion-Token: backend/.ingestion-token 內的值
```

請勿在投影片或錄影中顯示 token。

### 3. 切到 Cloud Run Logs

展示：

```text
TWSE 抓取
MOPS 下載與解析
子產業規則版本
Firestore persist counts
analysis run id
```

### 4. 顯示資料庫與 read API

```text
GET /api/v1/financial/companies/2330/metrics
GET /api/v1/financial/companies/2330/analysis-runs
GET /api/v1/financial/companies/2330/analysis/latest
```

### 5. 打開前端

前端顯示的 `analysis_run_id` 應與後端剛完成的 run 相同。

## 常見問題

### Billing 尚未驗證

程式與部署腳本已準備完成，但 Cloud Run、Firestore、Cloud Scheduler 無法在未連結有效 Billing 的專案正式建立。Billing 完成後從「部署 Cloud Run 與 Firestore」開始執行即可。

### Firestore 建立失敗

確認帳號具有 Owner 或 Datastore Owner 相關權限，並確認專案尚未存在不同模式的 `(default)` database。

### 管理端 endpoint 回傳 401

檢查 Cloud Scheduler job header 或 `/docs` 測試 header 是否使用 `backend/.ingestion-token` 的完整值。

### 管理端 endpoint 回傳 503

Production 缺少 `INGESTION_API_TOKEN`。重新執行 `bash deploy-cloud-run.sh`，不要手動把 placeholder 部署上線。

### MOPS 分析較慢

首次需要下載 3–5 份年度 iXBRL。Cloud Run timeout 已設定為 900 秒；四家公司分開排程，避免單一請求一次處理全部公司。

### Cloud Run 重啟後快取消失

`/tmp` 只存 iXBRL 暫存，重啟後消失是正常現象。正式 filings、facts、metrics、rules 與 snapshot 均存入 Firestore，不受 instance 回收影響。

## 不會自動執行的高風險操作

- 不會自動合併 Draft PR。
- 不會提交 `.ingestion-token`、`cloudrun.env.yaml` 或 `.env.production.local`。
- 不會由一般前端使用者呼叫管理端 refresh。
