# Firebase Hosting (`web.app`) 與 Cloud Run 串接指南

本文件對應 `feature/financial-statement-ai-mvp`。部署完成後的架構為：

```text
Firebase Hosting
https://<PROJECT_ID>.web.app
        │
        └── VITE_FINANCIAL_API_BASE_URL
                    ↓
Google Cloud Run / FastAPI
https://fintrust-alert-api-....run.app
                    │
                    ├── TWSE OpenAPI
                    └── MOPS Inline XBRL
```

第一版讓 Hosting 前端直接呼叫 Cloud Run，不使用 Hosting `/api/**` rewrite，避免 MOPS 首次抓取與解析受到 Hosting 轉送逾時限制。

## 已在程式庫準備好的檔案

- `firebase.json`：Vite `dist` 部署、React Router SPA rewrite、靜態資源快取。
- `backend/Dockerfile`：Python 3.12 Cloud Run 容器。
- `backend/.dockerignore`、`backend/.gcloudignore`：縮小部署內容。
- `backend/cloudrun.env.yaml.example`：Cloud Run 環境變數範本。
- `.env.production.example`：前端 Cloud Run URL 範本。

## 一、建立 Firebase／Google Cloud 專案

1. 在 Firebase Console 建立專案。
2. 專案 ID 會決定網址：`https://<PROJECT_ID>.web.app`。專案名稱與專案 ID 不一定相同，請記錄「專案 ID」。
3. 在同一專案連結 Cloud Billing。Cloud Run 與 Cloud Build 部署前通常需要啟用計費帳戶。
4. 建議在 Google Cloud Billing 建立預算通知。

下文以此代稱：

```text
PROJECT_ID=<你的 Firebase 專案 ID>
REGION=asia-east1
SERVICE=fintrust-alert-api
```

## 二、部署 FastAPI 到 Cloud Run

可以在 Windows 的 Google Cloud CLI 或 Google Cloud Shell 執行。

### 1. 取得 feature branch

```bash
git clone --branch feature/financial-statement-ai-mvp --single-branch https://github.com/UnaLu027/fintrust-alert.git
cd fintrust-alert/backend
```

### 2. 登入並選擇專案

```bash
gcloud auth login
gcloud config set project YOUR_FIREBASE_PROJECT_ID
```

在 Cloud Shell 中通常已登入，但仍要確認專案：

```bash
gcloud config get-value project
```

### 3. 啟用部署所需 API

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### 4. 建立正式環境變數檔

```bash
cp cloudrun.env.yaml.example cloudrun.env.yaml
```

將 `cloudrun.env.yaml` 的 `YOUR_FIREBASE_PROJECT_ID` 改成真正的專案 ID：

```yaml
CORS_ALLOW_ORIGINS: "https://YOUR_PROJECT_ID.web.app,https://YOUR_PROJECT_ID.firebaseapp.com"
MOPS_XBRL_CACHE_DIR: "/tmp/fintrust/mops_ixbrl_cache"
MOPS_XBRL_CACHE_TTL_HOURS: "24"
FINANCIAL_DATABASE_PATH: "/tmp/fintrust/financial_facts.sqlite3"
```

`cloudrun.env.yaml` 不要提交到 GitHub。

### 5. 從 `backend/` 部署

```bash
gcloud run deploy fintrust-alert-api \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated \
  --timeout 300 \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 3 \
  --env-vars-file cloudrun.env.yaml
```

Cloud Run 會讀取 `backend/Dockerfile`，建置映像並部署服務。

完成後記錄輸出的 Service URL，例如：

```text
https://fintrust-alert-api-xxxxxxxxxx-de.a.run.app
```

### 6. 後端驗收

依序打開：

```text
<CLOUD_RUN_URL>/
<CLOUD_RUN_URL>/docs
<CLOUD_RUN_URL>/api/v1/financial/health
<CLOUD_RUN_URL>/api/v1/financial/statements/2330/analyze
<CLOUD_RUN_URL>/api/v1/financial/statements/2330/history?years=3&end_year=2024
```

前四個應回傳 HTTP 200。歷史分析第一次需下載與解析 iXBRL，時間會較長。

## 三、建置並部署 Firebase Hosting

回到專案根目錄：

```bash
cd ..
```

### 1. 建立前端正式環境檔

```bash
cp .env.production.example .env.production.local
```

將內容改成剛剛取得的 Cloud Run URL，最後不要加 `/`：

```text
VITE_FINANCIAL_API_BASE_URL=https://fintrust-alert-api-xxxxxxxxxx-de.a.run.app
```

`.env.production.local` 已符合 `.gitignore` 的 `*.local` 規則，不會提交到 GitHub。

### 2. 安裝並建置

```bash
npm ci
npm run build
```

建置完成後應產生 `dist/`。

### 3. 登入 Firebase CLI

```bash
npx firebase-tools login
```

在 Cloud Shell 無法自動開瀏覽器時：

```bash
npx firebase-tools login --no-localhost
```

### 4. 綁定 Firebase 專案

```bash
npx firebase-tools use --add
```

從清單選擇同一個 Firebase 專案，並將 alias 設為：

```text
default
```

這一步會建立 `.firebaserc`。確認內容中的 project ID 正確後再提交；在尚未確認專案 ID 前不要手動猜測。

### 5. 部署 Hosting

```bash
npx firebase-tools deploy --only hosting
```

完成後應取得：

```text
https://YOUR_PROJECT_ID.web.app
https://YOUR_PROJECT_ID.firebaseapp.com
```

## 四、前後端完整驗收

1. 打開 `https://YOUR_PROJECT_ID.web.app`。
2. 登入後進入「財報規則引擎」。
3. 選擇台積電 2330。
4. 先按「分析 TWSE 最新資料」。
5. 再選 3 年並按「分析 MOPS 歷史財報」。
6. 使用瀏覽器開發者工具 Network 確認請求送往 Cloud Run，而不是 `localhost:8000`。
7. 再依序測試 2303、2454、3711。

## 五、常見問題

### 網頁顯示缺少 `VITE_FINANCIAL_API_BASE_URL`

代表 production build 前沒有建立 `.env.production.local`，或建立後沒有重新執行：

```bash
npm run build
npx firebase-tools deploy --only hosting
```

### 瀏覽器出現 CORS 錯誤

確認 Cloud Run 的 `CORS_ALLOW_ORIGINS` 與實際 Hosting 網址完全一致，網址末尾不要加 `/`。更新方式：

```bash
gcloud run services update fintrust-alert-api \
  --region asia-east1 \
  --env-vars-file backend/cloudrun.env.yaml
```

若目前位於 `backend/`，改用：

```bash
gcloud run services update fintrust-alert-api \
  --region asia-east1 \
  --env-vars-file cloudrun.env.yaml
```

### Cloud Run 建置失敗

確認部署指令是在 `backend/` 執行，因為 `Dockerfile` 與 `requirements.txt` 都位於該目錄。

### MOPS 歷史分析較慢

第一次會下載 3–5 份年度 iXBRL。容器使用 `/tmp` 作 24 小時快取，但 Cloud Run instance 被回收或重新部署後，暫存檔會消失。正式版可再接 Cloud Storage 作持久快取。

## 六、目前不做的事情

- 不先把 API rewrite 到 `web.app/api/**`。
- 不在尚未取得 Firebase project ID 前建立假的 `.firebaserc`。
- 不把 `.env.production.local` 或 `cloudrun.env.yaml` 提交到 GitHub。
- 不合併 Draft PR 到 `master`，直到線上四家公司皆完成驗收。
