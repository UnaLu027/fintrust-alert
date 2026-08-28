# Teacher-Aligned Financial Backend Development Plan

本文件把目前財報分析後端的開發順序，對應到老師最近的建議。開發策略是：先強化後端，但同時準備 Flask integration adapter，確保後續只要導入共享專案即可在統一介面展示財報證據。

## 目標定位

財報分析模組是金融資訊可信度系統的「官方量化證據層」，不是選股、估值或投資建議。系統只根據官方資料、可重現公式與規則結果產生財報證據，並提供給前端與 LLM 做摘要整合。

## Phase 1：整合介面與 API contract

目標：先回應老師提出的「統一介面」問題。

交付內容：

- `docs/integration-api-contract.md`
- `integrations/flask/fintrust_client.py`
- `integrations/flask/financial_routes.py`
- `integrations/flask/templates/_financial_evidence_card.html`
- `integrations/flask/static/financial-evidence.js`

驗收標準：

- 共享 Flask 專案可透過 proxy 呼叫 FastAPI。
- 前端可顯示 latest snapshot 的公司、整體狀態、摘要與 key metrics。
- Gemini key、FastAPI token、base URL 都只放後端環境變數。

## Phase 2：統一 LLM provider（Gemini）

目標：回應老師提出的「大語言模型 API 要統一」問題。

組內目前決定：

- 先統一使用 Gemini，不在此階段改成 OpenAI。
- `FINANCIAL_LLM_PROVIDER=gemini` 作為目前主要設定。
- `GEMINI_API_KEY` 只由後端環境變數或 Secret Manager 注入，不寫入 Git，也不放進前端 JavaScript。
- 既有 `anthropic` 與 `openai_compatible` provider 保留為架構彈性，但不是目前整合優先事項。

原則：

- LLM 只讀 structured evidence。
- LLM 不猜官方數字。
- LLM 不重算會計值。
- LLM 不修改 deterministic rule verdict。
- LLM 不提供投資建議。
- LLM 失敗時 deterministic 財報分析仍可使用。

## Phase 3：半導體子產業擴充

目標：回應老師提出的「半導體其他子產業，例如封裝測試，是否要納入」問題。

公司 seed：

| ticker | 公司 | 子產業 | 目標 |
| --- | --- | --- | --- |
| 2330 | 台積電 | 晶圓代工 | 既有 demo 基準 |
| 2303 | 聯電 | 晶圓代工 | 驗證 foundry rule 可重用 |
| 2454 | 聯發科 | IC 設計 | 驗證 AI v2 / IC design rule |
| 3711 | 日月光投控 | 封裝測試 | 回應老師封測建議 |

交付內容：

- `backend/scripts/smoke_semiconductor_companies.py`
- `npm run demo:semiconductor`
- `backend/tests/test_phase3_semiconductor_scope.py`

驗收標準：

- registry 明確包含 2330、2303、2454、3711。
- 不同子產業載入對應規則，不誤套 IC design rules。
- smoke script 能列出 status、available years、missing metrics、rule count、rule scope counts。
- 聯發科可額外驗證 deterministic AI v2；晶圓代工與封裝測試先保留 historical subindustry engine。

## Phase 4：法說會資料管線

目標：回應老師提出的「年度 XBRL 之外，要看法說會的新消息」問題。

第一版只做 metadata，不急著完整 PDF 摘要：

- 法說會日期
- 公司代號
- 標題
- 來源 URL
- 簡報或文件 URL
- 抓取時間

後續再做：

- PDF / HTML 文字抽取
- Gemini 摘要
- 展望、資本支出、庫存、需求、營收相關 claim extraction
- 與年度財報指標併列顯示

## Phase 5：重大訊息資料管線

目標：回應老師提出的「法說會之後再串重大訊息」問題。

第一版只做 metadata 與事件分類：

- 事件日期
- 公司代號
- 標題
- 事件類型
- 來源 URL
- 是否財務風險相關
- 關聯財務指標

## Phase 6：Official Evidence Aggregate API

最終提供一支整合 API：

```http
GET /api/v1/financial/companies/{ticker}/official-evidence
```

回傳：

- 年度財報 snapshot
- 最新法說會列表與摘要
- 最新重大訊息列表與分類
- official evidence summary
- limitations

這支 API 會讓共享前端只接一個官方證據包，不需要自己整合多種資料來源。

## 部署策略

短期：

- Codespaces / local FastAPI demo
- 共享 Flask 專案用 `FINTRUST_API_BASE_URL` 指向 FastAPI

中期：

- Flask 主系統與 FastAPI 財報服務都部署在同一個 Google Cloud 專案
- Cloud Run 管理服務
- Firestore 或其他雲端 DB 保存資料
- Cloud Scheduler 定期觸發 refresh
- Secret Manager 管理 Gemini key 與 ingestion token

## 不做的事

- 不把 API key 寫進前端。
- 不把 FastAPI 全部複製進 Flask `app.py`。
- 不讓 LLM 直接決定財報數字或投資建議。
- 不在 Phase 1 就重寫共享前端框架。
- 不在 Phase 2 改成 OpenAI，除非組內後續重新決定。
