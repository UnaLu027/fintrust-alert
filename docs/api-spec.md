# API 規格 — FinTrust Alert

## 慣例

- 前端 mock Base URL：`/api`；目前由 MSW 於瀏覽器端攔截。
- 財報證據服務 Base URL：`/api/v1/financial`；實作位於 `backend/`。
- 認證：除 `POST /api/auth/register`、`POST /api/auth/login` 外，其餘使用者 endpoint 皆需帶 `Authorization: Bearer <token>`。
- 錯誤格式統一為：

```json
{ "error": { "code": "invalid_credentials", "message": "帳號或密碼錯誤" } }
```

- 型別名稱對應 `src/types/*.ts`（`AnalysisResult`、`FinancialEvidenceResult`、`User`、`PushAlert`、`HistoryRecord`、`WatchlistItem` 等）。

---

## 使用者對外 API（目前由 MSW mock）

### 認證

| Method | Path | 說明 | Request | Response |
|---|---|---|---|---|
| POST | `/api/auth/register` | 註冊帳號並設定追蹤內容 | `RegisterPayload` | `{ token: string, user: User }` |
| POST | `/api/auth/login` | 登入 | `{ email, password }` | `{ token: string, user: User }` |
| POST | `/api/auth/logout` | 登出 | - | `{ ok: true }` |
| GET | `/api/auth/me` | 以 token 取回目前登入使用者 | - | `{ user: User }` |

### Dashboard（風險總覽）

| Method | Path | 說明 | Response |
|---|---|---|---|
| GET | `/api/dashboard/summary` | 5 張統計卡數字 | `DashboardSummary` |
| GET | `/api/dashboard/high-risk` | 今日高風險資訊列表 | `AnalysisResult[]` |

### 快速查證

| Method | Path | 說明 | Request | Response |
|---|---|---|---|---|
| POST | `/api/verify/analyze` | 送出查證條件，觸發分析 | `VerifyRequestPayload` | `{ analysisId: string }` |

`VerifyRequestPayload` 新增：

- `claimText`：使用者直接貼上的 X／Yahoo 財經文字。
- `analysisTypes` 可包含 `financial_statement_verification`。
- 財報查證仍保留 `company`、`ticker`、URL 與日期區間作為提示條件。

真實後端串接時，此 endpoint 應建立 `analysis_jobs`，並將可量化主張交給財報證據服務。不能由前端自行計算官方數值。

### 分析結果

| Method | Path | 說明 | Response |
|---|---|---|---|
| GET | `/api/analysis/:id` | 取得完整分析結果；若可量化，包含 `financialEvidence` | `AnalysisResult` |

`financialEvidence` 包含：

- claim-level 結果，而非整篇文章只有一個真假標籤
- 抽取後的公司、半導體子產業、指標、期間、方向與數值
- 官方本期值、比較值、公式、重新計算結果及容許誤差
- supported／partially_supported／contradicted／insufficient_evidence／not_applicable
- 來源連結、資料涵蓋限制與 `isDemo`

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

## 財報證據服務 API（FastAPI MVP）

| Method | Path | 說明 | Request | Response |
|---|---|---|---|---|
| GET | `/api/v1/financial/health` | 回報方法、產業及歷史 XBRL readiness | - | `HealthResponse` |
| GET | `/api/v1/financial/companies` | 取得可擴充的半導體公司 seed registry | - | `CompanyListResponse` |
| POST | `/api/v1/financial/claims/extract` | 將中文財務敘述轉成結構化主張 | `ClaimExtractionRequest` | `ExtractedFinancialClaim` |
| POST | `/api/v1/financial/claims/verify` | 查詢 facts 並以確定性公式驗證 | `ClaimVerificationRequest` | `ClaimVerificationResult` |
| POST | `/api/v1/financial/facts/ingest` | 匯入已正規化的官方 XBRL／OpenAPI facts | `FactIngestRequest` | `{ inserted, warning }` |

### 查證原則

- 只有明確公司、指標與期間才進入量化查證。
- 「今年」「最近」等相對期間不自動猜測。
- 比較期缺失、官方資料未匯入或單位無法對齊時回傳 `insufficient_evidence`。
- 數值與公式由 deterministic code 執行，生成式模型不直接決定官方數字。
- seed registry 涵蓋半導體不同子產業；未來 peer comparison 僅允許同一子產業。

---

## 資料擷取端點（整體系統規劃）

這些 endpoint 不面向一般使用者，正式版應採 service-to-service API key 驗證。

| Method | Path | 呼叫方 | 說明 |
|---|---|---|---|
| POST | `/api/ingest/raw-item` | X／Yahoo 財經擷取程式 | 寫入待查證文字與來源欄位 |
| POST | `/api/v1/financial/facts/ingest` | MOPS XBRL／TWSE adapter | 寫入正規化官方財務 facts |
| POST | `/api/ingest/analysis-result` | 模型與證據服務 | 回寫風險、來源比較與財報查證結果 |
| POST | `/api/ingest/webhook/job-failed` | 內部服務 | 任務失敗回呼 |
| GET | `/api/ingest/jobs/:id/status` | 內部服務／後台 | 查詢分析工作狀態 |

```text
X／Yahoo raw item → claim detection／extraction
                    ↓
MOPS／TWSE facts → deterministic recalculation
                    ↓
claim-level verdict + evidence attribution
                    ↓
analysis result → watchlist matching → alerts
```

## 版本與驗證備註

- 使用者端 API：JWT／session token（目前 mock 以 `Bearer token-<userId>` 模擬）。
- 擷取端 API：正式部署前必須增加獨立 service API key。
- `facts/ingest` 目前只接受 normalized facts；MOPS Inline XBRL 自動下載與 taxonomy mapping 尚未完成，不得標示為已完成。
