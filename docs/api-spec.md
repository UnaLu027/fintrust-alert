# API 規格 — FinTrust Alert

## 慣例

- 前端 mock Base URL：`/api`；目前由 MSW 於瀏覽器端攔截。
- 財報規則引擎 Base URL：`/api/v1/financial`；實作位於 `backend/`。
- 認證：除 `POST /api/auth/register`、`POST /api/auth/login` 外，其餘使用者 endpoint 皆需帶 `Authorization: Bearer <token>`。
- 錯誤格式統一為：

```json
{ "error": { "code": "invalid_credentials", "message": "帳號或密碼錯誤" } }
```

- 型別名稱對應 `src/types/*.ts`。

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

`VerifyRequestPayload` 可包含：

- `claimText`：使用者直接貼上的 X／Yahoo 財經文字。
- `analysisTypes`：可包含 `financial_statement_verification`。
- `company`、`ticker`、URL 與日期區間等提示條件。

真實後端串接時，此 endpoint 應建立 `analysis_jobs`，再將量化主張交給財報證據服務；官方數值不得由前端或生成式模型自行猜測。

### 分析結果

| Method | Path | 說明 | Response |
|---|---|---|---|
| GET | `/api/analysis/:id` | 取得完整分析結果；若可量化，包含 `financialEvidence` | `AnalysisResult` |

`financialEvidence` 包含 claim-level 結果、公司與子產業、指標、期間、公式、官方數值、容許誤差、來源及資料限制。

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
| GET | `/api/watchlist` | 取得追蹤清單與提醒偏好 | - | watchlist response |
| PUT | `/api/watchlist` | 更新追蹤公司、產業、關鍵字與提醒偏好 | watchlist payload | 同 GET |

---

## 半導體財報規則引擎 API（FastAPI MVP）

| Method | Path | 說明 | Request | Response |
|---|---|---|---|---|
| GET | `/api/v1/financial/health` | 回報 TWSE、規則引擎與 MOPS iXBRL adapter readiness | - | `HealthResponse` |
| GET | `/api/v1/financial/companies` | 半導體公司 seed registry | - | `CompanyListResponse` |
| GET | `/api/v1/financial/rules` | 最新快照規則版本與門檻 | - | `RuleCatalogResponse` |
| GET | `/api/v1/financial/statements/{ticker}/analyze` | 抓取 TWSE 最新快照並執行規則 | - | `FinancialStatementAnalysisReport` |
| GET | `/api/v1/financial/statements/{ticker}/history?years=5` | 抓取 MOPS 年度合併 iXBRL 並執行 3–5 年趨勢規則 | `years=3..5`, optional `end_year` | `HistoricalFinancialAnalysisReport` |
| POST | `/api/v1/financial/claims/extract` | 中文財務敘述轉結構化主張 | `ClaimExtractionRequest` | `ExtractedFinancialClaim` |
| POST | `/api/v1/financial/claims/verify` | 查詢 facts 並以確定性公式驗證 | `ClaimVerificationRequest` | `ClaimVerificationResult` |
| POST | `/api/v1/financial/facts/ingest` | 匯入已正規化官方 facts | `FactIngestRequest` | `{ inserted, warning }` |

### MOPS 歷史端點參數

- `years`：只接受 3、4 或 5，預設 5。
- `end_year`：西元財報年度，例如 `2025`；省略時以最近已完成年度開始向前抓取。
- 第一版只抓第 4 季／年度合併財報，避免把 Q2、Q3 累計值當成單季。
- 某年度下載、解析、taxonomy mapping 或 context 對應失敗時，該年度保留 `error`／`missing`，不以零值補齊。

### `HistoricalFinancialAnalysisReport`

主要欄位：

- `requested_years`、`available_years`、`start_year`、`end_year`
- `periods[]`：每年度來源、狀態、已映射／缺少欄位、concept matches 與 warnings
- `trend_metrics[]`：各年度數值、公式、最新年增率或百分點變化
- `rule_results[]`：規則編號、嚴重程度、門檻、解釋與證據年度
- `limitations[]`：資料與方法限制

### 財報規則原則

- 產業固定為半導體；同業比較只允許相同子產業。
- TWSE 用於最新快照；MOPS Inline XBRL 用於 3–5 年歷史資料。
- MOPS adapter 使用 annual context 與 instant context 選取當年度 facts，排除同文件前期比較值。
- 所有比率、年增率、現金流與規則結果由 deterministic code 計算。
- 無法確認公司、期間、taxonomy concept、context 或單位時回傳資料不足。
- 規則門檻為版本化 MVP 參數，正式研究版仍需子產業中位數與 MAD 校準。
- 所有結果均為財務資訊整理與風險提示，不構成投資建議。

---

## 資料擷取端點（整體系統規劃）

正式版的 service-to-service 擷取端點應使用獨立 API key。

| Method | Path | 呼叫方 | 說明 |
|---|---|---|---|
| POST | `/api/ingest/raw-item` | X／Yahoo 財經擷取程式 | 寫入待查證文字與來源欄位 |
| GET | `/api/v1/financial/statements/{ticker}/history` | 財報規則引擎／排程 | 自動下載與解析 MOPS iXBRL |
| POST | `/api/v1/financial/facts/ingest` | 其他官方資料 adapter | 寫入正規化官方 facts |
| POST | `/api/ingest/analysis-result` | 模型與證據服務 | 回寫風險、來源比較與財報結果 |
| POST | `/api/ingest/webhook/job-failed` | 內部服務 | 任務失敗回呼 |
| GET | `/api/ingest/jobs/:id/status` | 內部服務／後台 | 查詢工作狀態 |

```text
TWSE 最新快照 ─┐
                 ├→ deterministic metrics → versioned rules → analysis result
MOPS annual iXBRL ┘
```

## 版本與驗證備註

- 使用者端 API：JWT／session token（目前 mock 以 `Bearer token-<userId>` 模擬）。
- MOPS iXBRL adapter 使用 `twmops[xbrl]` 與 Arelle；正式部署仍須遵守 MOPS 使用條款與合理請求頻率。
- 歷史 iXBRL 已接入；尚未完成季度累計轉單季、重編版本追蹤與同子產業統計基準。
