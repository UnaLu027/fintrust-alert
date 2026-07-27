# Firebase Hosting (`web.app`) 與 Cloud Run 串接指南

本文件對應 `feature/financial-statement-ai-mvp`，目前已綁定 Firebase Project ID：

```text
fintrust-alert
```

部署完成後的架構為：

```text
Firebase Hosting
https://fintrust-alert.web.app
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

- `.firebaserc`：已綁定 `fintrust-alert`。
- `firebase.json`：Vite `dist` 部署、React Router SPA rewrite、靜態資源快取。
- `backend/Dockerfile`：Python 3.12 Cloud Run 容器。
- `backend/.dockerignore`、`backend/.gcloudignore`：縮小部署內容。
- `backend/cloudrun.env.yaml.example`：已填入 `fintrust-alert.web.app` 與 `fintrust-alert.firebaseapp.com`。
- `backend/deploy-cloud-run.sh`：Cloud Shell 一鍵部署腳本。
- `.env.production.example`：前端 Cloud Run URL 範本。

## 一、確認 Firebase／Google Cloud 專案

目前固定使用：

```text
PROJECT_ID=fintrust-alert
REGION=asia-east1
SERVICE=fintrust-alert-api
```

預計前端網址：

```text
https://fintrust-alert.web.app
https://fintrust-alert.firebaseapp.com
```

部署 Cloud Run 前，必須在同一個 Firebase／Google Cloud 專案連結 Cloud Billing，並建議建立預算通知。

## 二、部署 FastAPI 到 Cloud Run

建議直接使用瀏覽器中的 Google Cloud Shell，不必先在 Windows 安裝 Google Cloud CLI。

### 1. 開啟 Cloud Shell

登入 Google Cloud Console，右上角點擊終端機圖示「啟用 Cloud Shell」。

先確認目前專案：

```bash
gcloud config get-value project
```

若不是 `fintrust-alert`，執行：

```bash
gcloud config set project fintrust-alert
```

### 2. 取得 feature branch

```bash
git clone --branch feature/financial-statement-ai-mvp --single-branch https://github.com/UnaLu027/fintrust-alert.git
cd fintrust-alert/backend
```

### 3. 執行部署腳本

```bash
bash deploy-cloud-run.sh
```

腳本會自動：

1. 選擇 `fintrust-alert` 專案。
2. 啟用 Cloud Run、Cloud Build、Artifact Registry API。
3. 複製 `cloudrun.env.yaml.example` 為 `cloudrun.env.yaml`。
4. 使用 `backend/Dockerfile` 建置並部署。
5. 設定 300 秒逾時、2 GiB 記憶體與最多 3 個 instances。

等同的完整指令為：

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

完成後記錄輸出的 Service URL，例如：

```text
https://fintrust-alert-api-xxxxxxxxxx-de.a.run.app
```

### 4. 後端驗收

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

Cloud Run 驗收成功後，在同一個 Cloud Shell 執行：

```bash
cd ..
```

### 1. 建立前端正式環境檔

```bash
cp .env.production.example .env.production.local
```

編輯：

```bash
nano .env.production.local
```

填入剛剛取得的 Cloud Run URL，最後不要加 `/`：

```text
VITE_FINANCIAL_API_BASE_URL=https://fintrust-alert-api-xxxxxxxxxx-de.a.run.app
```

儲存方式：

```text
Ctrl + O
Enter
Ctrl + X
```

`.env.production.local` 符合 `.gitignore` 的 `*.local` 規則，不會提交到 GitHub。

### 2. 登入 Firebase CLI

```bash
npx firebase-tools login --no-localhost
```

Cloud Shell 會顯示登入網址；開啟網址、允許權限，再把驗證碼貼回終端機。

### 3. 建置並部署 Hosting

由於 `.firebaserc` 已綁定 `fintrust-alert`，不需要再執行 `firebase use --add`。

執行：

```bash
npm ci
npm run deploy:hosting
```

`deploy:hosting` 會自動：

```text
npm run build
→ 產生 dist/
→ 部署到 Firebase Hosting
```

完成後應取得：

```text
https://fintrust-alert.web.app
https://fintrust-alert.firebaseapp.com
```

## 四、前後端完整驗收

1. 打開 `https://fintrust-alert.web.app`。
2. 登入後進入「財報規則引擎」。
3. 選擇台積電 2330。
4. 先按「分析 TWSE 最新資料」。
5. 再選 3 年並按「分析 MOPS 歷史財報」。
6. 使用瀏覽器開發者工具 Network 確認請求送往 Cloud Run，而不是 `localhost:8000`。
7. 再依序測試 2303、2454、3711。

## 五、常見問題

### Cloud Run 顯示沒有 Billing

必須先在 `fintrust-alert` 專案連結 Cloud Billing，再重新執行：

```bash
bash deploy-cloud-run.sh
```

### 網頁顯示缺少 `VITE_FINANCIAL_API_BASE_URL`

代表 production build 前沒有建立 `.env.production.local`，或建立後沒有重新建置部署：

```bash
npm run deploy:hosting
```

### 瀏覽器出現 CORS 錯誤

目前範本已設定：

```text
https://fintrust-alert.web.app
https://fintrust-alert.firebaseapp.com
```

更新 Cloud Run 環境變數：

```bash
cd backend
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
- 不把 `.env.production.local` 或 `cloudrun.env.yaml` 提交到 GitHub。
- 不合併 Draft PR 到 `master`，直到線上四家公司皆完成驗收。
