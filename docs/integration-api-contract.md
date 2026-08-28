# Financial Evidence Integration API Contract

本文件定義財報分析後端與共享 Flask 專案的整合邊界。目標是回應老師提出的「統一介面、開始整合」要求：共享專案只需要透過 HTTP JSON API 讀取財報證據，不需要搬移或重寫 FastAPI 內部的 MOPS / TWSE 抓取、財報正規化、規則引擎與 LLM 流程。

## 系統角色

| 層級 | 元件 | 職責 |
| --- | --- | --- |
| 統一介面 | 共享 Flask 專案 | 使用者入口、搜尋結果、官方證據卡、分析紀錄頁面 |
| 財報服務 | `fintrust-alert` FastAPI | 官方財報取得、資料正規化、指標計算、規則引擎、latest snapshot |
| 整合層 | `integrations/flask` adapter | 在 Flask 內提供 proxy routes，避免前端直接接觸 FastAPI URL 與 token |
| LLM | 組內統一 provider | 只接收已計算完成的 structured evidence，不猜數字、不改規則結果 |
| 資料層 | SQLite / Firestore | SQLite 用於 Codespaces 與本機 demo；Firestore 或其他雲端 DB 用於正式部署 |

## 整合原則

1. **FastAPI 不併入 Flask app.py**：財報分析維持獨立服務，避免把官方資料抓取、XBRL 解析、規則引擎塞進展示型前端。
2. **Flask 作為 BFF / proxy**：瀏覽器只呼叫共享 Flask 專案，由 Flask 後端代為呼叫 FastAPI。
3. **API key 與 ingestion token 不進前端**：OpenAI key、FastAPI token、雲端設定都只放在後端環境變數。
4. **先接 latest snapshot**：第一版前端只需接 `analysis/latest`，先證明財報證據能出現在統一介面。
5. **預留官方資料擴充**：年度財報為第一層；後續新增法說會與重大訊息，形成更即時的官方證據包。

## Base URL

開發環境：

```env
FINTRUST_API_BASE_URL=http://127.0.0.1:8000
```

部署環境：

```env
FINTRUST_API_BASE_URL=https://<cloud-run-fintrust-api-url>
```

## 前端第一階段必接 API

### 1. 取得最新財報分析快照

共享 Flask proxy：

```http
GET /api/financial/companies/{ticker}/analysis/latest
```

FastAPI upstream：

```http
GET /api/v1/financial/companies/{ticker}/analysis/latest
```

用途：在共享前端顯示「官方財報證據」卡片。

前端建議顯示欄位：

- `company_name`
- `ticker`
- `subindustry`
- `overall_severity`
- `summary`
- `key_metrics[]`
  - `label`
  - `latest_value`
  - `unit`
  - `change_percent`
  - `formula`
  - `period_values`
- `rule_cards[]`
- `sources[]`
- `limitations[]`

錯誤處理：

- `404`：尚未有快照，顯示「尚未完成官方財報分析」。
- `502`：FastAPI 或外部來源暫時不可用，顯示「財報服務暫時無法連線」。
- 其他錯誤：保留使用者查詢結果，但隱藏或降級財報證據區塊。

### 2. 取得最新指標列表

共享 Flask proxy：

```http
GET /api/financial/companies/{ticker}/metrics?latest_only=true&limit=1000
```

FastAPI upstream：

```http
GET /api/v1/financial/companies/{ticker}/metrics?latest_only=true&limit=1000
```

用途：給前端做進階指標列表或 dashboard。

### 3. 取得分析執行紀錄

共享 Flask proxy：

```http
GET /api/financial/companies/{ticker}/analysis-runs
```

FastAPI upstream：

```http
GET /api/v1/financial/companies/{ticker}/analysis-runs
```

用途：對應共享專案的分析紀錄頁，讓老師看到每次 pipeline 的 `run_id`、觸發方式、完成時間與狀態。

## 管理端 API

### 觸發官方財報分析

共享 Flask proxy：

```http
POST /api/financial/admin/companies/{ticker}/refresh
```

FastAPI upstream：

```http
POST /api/v1/financial/admin/companies/{ticker}/refresh?years=3&end_year=2024&trigger=manual&source_mode=official
```

建議只放在管理端或 demo 控制台，不要開放給一般使用者。

## 老師需求對照

| 老師建議 | 目前 API / 後續設計 |
| --- | --- |
| 統一介面、開始整合 | Flask proxy + 財報證據卡接 `analysis/latest` |
| 半導體不只台積電 | `companies` 與 ticker-based APIs 保留 2330、2303、2454、3711 擴充空間 |
| 年度 XBRL 是第一步 | MOPS iXBRL pipeline 仍是財報量化主資料來源 |
| 增加法說會 | 後續新增 `conferences` APIs，先抓 metadata，再做文件摘要 |
| 增加重大訊息 | 後續新增 `material-events` APIs，先做事件分類與官方來源連結 |
| 統一 LLM API | LLM provider layer 統一由後端環境變數設定；前端不直接呼叫 OpenAI |

## 後續預留 API

```http
POST /api/v1/financial/admin/companies/{ticker}/conferences/refresh
GET  /api/v1/financial/companies/{ticker}/conferences
GET  /api/v1/financial/companies/{ticker}/conferences/latest

POST /api/v1/financial/admin/companies/{ticker}/material-events/refresh
GET  /api/v1/financial/companies/{ticker}/material-events
GET  /api/v1/financial/companies/{ticker}/material-events/latest

GET  /api/v1/financial/companies/{ticker}/official-evidence
```

`official-evidence` 會是長期最適合前端接的一支 aggregate API，整合年度財報、法說會與重大訊息。
