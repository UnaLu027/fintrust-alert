# Financial Evidence Integration API Contract

本文件定義財報分析後端與共享 Flask 專案的整合邊界。目標是回應老師提出的「統一介面、開始整合」要求：共享專案只需要透過 HTTP JSON API 讀取財報證據，不需要搬移或重寫 FastAPI 內部的 MOPS / TWSE 抓取、財報正規化、規則引擎、法說會 metadata、重大訊息 metadata 與 LLM 流程。

## 系統角色

| 層級 | 元件 | 職責 |
| --- | --- | --- |
| 統一介面 | 共享 Flask 專案 | 使用者入口、搜尋結果、官方證據卡、分析紀錄頁面 |
| 財報服務 | `fintrust-alert` FastAPI | 官方財報取得、資料正規化、指標計算、規則引擎、latest snapshot、法說會 / 重大訊息 metadata |
| 整合層 | `integrations/flask` adapter | 在 Flask 內提供 proxy routes，避免前端直接接觸 FastAPI URL 與 token |
| LLM | 組內統一 Gemini provider | 只接收已計算完成的 structured evidence，不猜數字、不改規則結果 |
| 資料層 | SQLite / Firestore | SQLite 用於 Codespaces 與本機 demo；Firestore 或其他雲端 DB 用於正式部署 |

## 整合原則

1. **FastAPI 不併入 Flask app.py**：財報分析維持獨立服務，避免把官方資料抓取、XBRL 解析、規則引擎塞進展示型前端。
2. **Flask 作為 BFF / proxy**：瀏覽器只呼叫共享 Flask 專案，由 Flask 後端代為呼叫 FastAPI。
3. **API key 與 ingestion token 不進前端**：Gemini key、FastAPI token、雲端設定都只放在後端環境變數。
4. **優先接 official-evidence**：共享前端第一版可直接讀取年度財報 snapshot、法說會 metadata 與重大訊息 metadata。
5. **清楚標示 metadata MVP**：法說會與重大訊息目前先做查詢入口、事件分類與關聯指標，不宣稱完成全文解析。

## Base URL

開發環境：

```env
FINTRUST_API_BASE_URL=http://127.0.0.1:8000
```

部署環境：

```env
FINTRUST_API_BASE_URL=https://<cloud-run-fintrust-api-url>
```

## 前端第一階段優先 API

### 1. 取得官方證據整合包

共享 Flask proxy：

```http
GET /api/financial/companies/{ticker}/official-evidence
```

FastAPI upstream：

```http
GET /api/v1/financial/companies/{ticker}/official-evidence
```

用途：在共享前端顯示「官方財報證據」與「近期官方事件」。

前端建議顯示欄位：

- `company_name`
- `ticker`
- `subindustry`
- `readiness`
- `official_evidence_summary`
- `financial_snapshot`
  - `overall_severity`
  - `summary`
  - `key_metrics[]`
  - `rule_cards[]`
- `investor_conferences[]`
  - `title`
  - `source_url`
  - `extracted_topics[]`
  - `related_metrics[]`
  - `status`
- `material_events[]`
  - `title`
  - `category`
  - `source_url`
  - `related_metrics[]`
  - `risk_related`
- `limitations[]`
- `sources[]`

錯誤處理：

- `readiness=needs_refresh`：尚未有財報 snapshot；可顯示法說會 / 重大訊息入口，並提示管理端先 refresh 財報。
- `metadata_only`：代表目前只完成官方查詢入口與分類，不代表已完成 PDF / 公告全文解析。
- `502`：FastAPI 或外部來源暫時不可用，顯示「財報服務暫時無法連線」。

### 2. 取得最新財報分析快照

共享 Flask proxy：

```http
GET /api/financial/companies/{ticker}/analysis/latest
```

FastAPI upstream：

```http
GET /api/v1/financial/companies/{ticker}/analysis/latest
```

用途：只顯示年度財報 latest snapshot 時使用。

### 3. 取得最新指標列表

共享 Flask proxy：

```http
GET /api/financial/companies/{ticker}/metrics?latest_only=true&limit=1000
```

FastAPI upstream：

```http
GET /api/v1/financial/companies/{ticker}/metrics?latest_only=true&limit=1000
```

用途：給前端做進階指標列表或 dashboard。

### 4. 取得分析執行紀錄

共享 Flask proxy：

```http
GET /api/financial/companies/{ticker}/analysis-runs
```

FastAPI upstream：

```http
GET /api/v1/financial/companies/{ticker}/analysis-runs
```

用途：對應共享專案的分析紀錄頁，讓老師看到每次 pipeline 的 `run_id`、觸發方式、完成時間與狀態。

## 官方事件 API

### 法說會 metadata

```http
GET /api/v1/financial/companies/{ticker}/conferences
```

目前回傳 MOPS 法說會查詢入口與子產業關聯指標。後續可擴充 PDF / HTML / 影音逐字稿摘要。

### 重大訊息 metadata / classification

```http
GET /api/v1/financial/companies/{ticker}/material-events?year=2024&title=董事會決議擴產
```

目前回傳 MOPS 重大訊息查詢入口與保守事件分類。`title` 參數主要給整合測試與 demo 使用；正式版會改由 scraper 取得公告標題。

## 管理端 API

### 觸發官方財報分析

共享 Flask proxy：

```http
POST /api/financial/admin/companies/{ticker}/refresh
```

FastAPI upstream：

```http
POST /api/v1/financial/admin/companies/{ticker}/refresh
```

此 endpoint 應只提供管理端使用。`X-Ingestion-Token` 只存在 Flask server 或雲端 Secret 中，不能進前端。