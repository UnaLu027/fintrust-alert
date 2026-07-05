# API 規格 — FinTrust Alert

## 慣例

- Base URL：`/api`（目前由 MSW 於瀏覽器端攔截 mock；未來接真實後端時只需更換 base URL，前端呼叫方式不變）
- 認證：除 `POST /api/auth/register`、`POST /api/auth/login` 外，其餘 endpoint 皆需帶 `Authorization: Bearer <token>`
- 錯誤格式統一為：

```json
{ "error": { "code": "invalid_credentials", "message": "帳號或密碼錯誤" } }
```

- 型別名稱對應 `src/types/*.ts`（`AnalysisResult`、`User`、`PushAlert`、`HistoryRecord`、`WatchlistItem` 等）

---

## 使用者對外 API（已於 MSW 完整 mock）

### 認證

| Method | Path | 說明 | Request | Response |
|---|---|---|---|---|
| POST | `/api/auth/register` | 註冊帳號並設定追蹤內容 | `RegisterPayload` | `{ token: string, user: User }` |
| POST | `/api/auth/login` | 登入 | `{ email, password }` | `{ token: string, user: User }` |
| POST | `/api/auth/logout` | 登出 | - | `{ ok: true }` |
| GET | `/api/auth/me` | 以 token 取回目前登入使用者（供刷新頁面時還原登入狀態） | - | `{ user: User }` |

### Dashboard（風險總覽）

| Method | Path | 說明 | Response |
|---|---|---|---|
| GET | `/api/dashboard/summary` | 5 張統計卡數字 | `DashboardSummary` |
| GET | `/api/dashboard/high-risk` | 今日高風險資訊列表 | `AnalysisResult[]` |

### 快速查證

| Method | Path | 說明 | Request | Response |
|---|---|---|---|---|
| POST | `/api/verify/analyze` | 送出查證條件，觸發分析 | `VerifyRequestPayload` | `{ analysisId: string }` |

> 真實後端串接時，此 endpoint 應改為：建立 `analysis_jobs`（若命中既有 `raw_items` 可重用），非同步呼叫 Python 模型服務，並回傳 `analysisId` 供前端輪詢或等待完成。

### 分析結果

| Method | Path | 說明 | Response |
|---|---|---|---|
| GET | `/api/analysis/:id` | 取得完整分析結果（含風險原因、三來源比對） | `AnalysisResult` |

### 追蹤與推播提醒

| Method | Path | 說明 | Response |
|---|---|---|---|
| GET | `/api/alerts` | 取得目前使用者的推播提醒列表 | `PushAlert[]` |

### 分析紀錄

| Method | Path | 說明 | Request | Response |
|---|---|---|---|---|
| GET | `/api/history` | 取得目前使用者的分析紀錄 | - | `HistoryRecord[]` |
| POST | `/api/history/:id/track` | 將某筆紀錄加入追蹤 | - | `HistoryRecord` |
| DELETE | `/api/history/:id` | 刪除某筆分析紀錄 | - | `{ ok: true }` |

### 追蹤清單／提醒偏好

| Method | Path | 說明 | Request | Response |
|---|---|---|---|---|
| GET | `/api/watchlist` | 取得目前使用者的追蹤清單與提醒偏好 | - | `{ items: WatchlistItem[], alertFrequency, alertTypes }` |
| PUT | `/api/watchlist` | 更新追蹤公司／產業／關鍵字與提醒偏好 | `{ watchedCompanies, watchedIndustries, watchedKeywords, alertFrequency, alertTypes }` | 同 GET |

---

## 未來資料擷取端點（尚未 mock，供後端／爬蟲／模型團隊參考）

這些 endpoint 不面向一般使用者，改用 service-to-service API key 驗證（例如 `X-Ingest-Key` header），而非使用者 JWT。

| Method | Path | 呼叫方 | 說明 |
|---|---|---|---|
| POST | `/api/ingest/raw-item` | X 爬蟲／Yahoo 財經爬蟲／MOPS 擷取程式 | 寫入一筆 `raw_items`，欄位對應 `docs/schema.md` 的 `raw_items` 表。回傳 `{ rawItemId }`，並觸發建立對應的 `analysis_jobs` |
| POST | `/api/ingest/analysis-result` | Python 真偽判斷模型服務 | 模型完成一個 `analysis_jobs` 後回寫結果：`riskLevel`、`riskScore`、`verificationStatus`、`riskReasons[]`、`sourceComparisons[]` 等，寫入 `analyses`／`risk_reasons`／`source_comparisons`，並觸發使用者 watchlist 比對以產生 `push_alerts` |
| POST | `/api/ingest/webhook/job-failed` | Python 模型服務 | 任務失敗回呼，供錯誤追蹤與重試機制使用 |
| GET | `/api/ingest/jobs/:id/status` | 內部服務／後台 | 輪詢 `analysis_jobs` 狀態（若未採用 webhook 通知） |

### 資料流對應

```
POST /api/ingest/raw-item        → raw_items 新增一筆
                                  → 系統建立 analysis_jobs（status=queued）
Python 模型服務取件處理           → analysis_jobs.status=running
POST /api/ingest/analysis-result → analyses / risk_reasons / source_comparisons 寫入
                                  → analysis_jobs.status=done
                                  → 比對 watchlist_items，產生 push_alerts（若符合條件）
```

## 版本與驗證備註

- 使用者端 API：JWT／session token（目前 mock 以 `Bearer token-<userId>` 模擬）
- 擷取端 API（`/api/ingest/*`）：獨立的 service API key，與使用者驗證機制分開管理，避免爬蟲/模型服務的憑證與一般使用者權限混用
