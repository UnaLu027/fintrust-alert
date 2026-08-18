# AI 財報分析引擎 v2：IC 設計產業化與自動 Pipeline

## 1. 這一版修正了什麼

v1 將 24 條規則都放在 IC 設計規則檔中，容易讓人誤以為所有規則都是 IC 設計產業專屬標準。v2 改成三層規則：

1. `common`：跨產業都成立的基本面與會計關係。
2. `semiconductor`：半導體常見的產品組合、存貨循環、現金流分析。
3. `ic_design`：IC 設計特別重視的研發投入、產品組合、庫存／應收週轉與研發轉化。

總規則數仍為 24 條，但現在可以直接由 `rule_scope_counts` 看出：

- common：10
- semiconductor：4
- ic_design：10

因此簡報時應稱為「24 條分層分析規則」，而不是「24 條 IC 設計產業標準」。

## 2. 產業依據

IC 設計 v2 的規則設計以聯發科官方投資人資料呈現方式作為重要參考：

- MediaTek 為 fabless semiconductor company，研發是核心投入。
- 官方永續／創新資料設定年度研發投入目標，支持 R&D 作為 IC 設計核心分析軸。
- 2024 Q3 官方財報說明毛利率改善主要來自 product mix；同季營業費用增加主要來自較高 R&D investment。
- 官方財報固定揭露 accounts receivable turnover days、inventory turnover days 與 operating cash flow，因此 v2 新增應收與存貨週轉天數，不再只靠期末存貨成長率作 proxy。

規則中的 `evidence_basis` 與 `evidence_references` 會保留這些設計依據，方便後台與簡報追溯。

## 3. 門檻治理

每條規則新增 `threshold_basis`。目前主要類型：

- `directional`：只判斷增加／減少或正／負，不依賴任意數值門檻。
- `accounting_directional`：依會計數值方向，例如淨利為正但 OCF 為負。
- `accounting_identity_plus_trend`：例如 current ratio 100% 搭配下降趨勢。
- `heuristic_mvp`：15 天、20 個百分點、0.8 倍等目前僅供 MVP 架構驗證。

`heuristic_mvp` 不得宣稱為 IC 設計產業公認標準。下一階段需要以公司自身 3–5 年分布與同子產業 peer baseline（median / MAD）校準。

## 4. R&D 規則修正

### 不再使用

`R&D expense ↑ AND R&D intensity ↑ -> positive`

因為 IC 設計本來就高度研發密集，研發增加本身不能直接代表基本面改善。

### v2

- `IC_RD_001`：研發費用增加、研發強度大致維持，只標記「投入持續」，severity 為 normal。
- `IC_RD_002`：只有研發費用本身未成長且 R&D intensity 明顯下降，才列 attention，避免營收快速成長使 intensity 被動下降造成誤判。
- `IC_RD_003`：高研發投入 + 營收衰退 + 存貨相對營收背離 + cash conversion 弱，才列 high attention。

這種設計把研發的直接衡量與營收、存貨、現金流的間接衡量分開。

## 5. 新增 IC 設計營運效率指標

MOPS iXBRL mapping 新增：

- `cost_of_goods_sold`
- `accounts_receivable`

Historical Metric Engine 新增：

- `inventory_turnover_days = 平均存貨 / |年度營業成本| * 365`
- `receivable_turnover_days = 平均應收帳款 / 年度營收 * 365`

Feature Engine 會為所有可比較指標建立 `*_change_absolute`，因此規則可以監控「週轉天數增加幾天」，而不是只看百分比變化。

如果 taxonomy 無法可靠映射，欄位保持 missing，依賴規則回傳 `insufficient_data`，不以零值或 LLM 猜測補齊。

## 6. 自動化 Pipeline

Scheduler 原本每天依序呼叫四家公司 refresh：

```text
Cloud Scheduler
  -> POST /api/v1/financial/admin/companies/{ticker}/refresh
  -> TWSE latest
  -> MOPS 3–5 year annual iXBRL
  -> normalize
  -> historical metrics
  -> historical rules
  -> AI Financial Analysis v2 (IC 設計目前支援 2454)
       -> feature engine
       -> common + semiconductor + ic_design rules
       -> 8 dimension assessments
       -> optional LLM synthesis
  -> frontend snapshot
  -> SQLite / Firestore persistence
```

不需要人工輸入財報數字。

### LLM 自動執行

正式 `official` refresh 預設允許 LLM：

- `FINANCIAL_AI_AUTO_LLM_ENABLED=true`
- `FINANCIAL_LLM_ENDPOINT`
- `FINANCIAL_LLM_API_KEY`
- `FINANCIAL_LLM_MODEL`

若模型沒有設定，automatic pipeline 仍會完成 deterministic features、24 rules、8 dimensions，`llm_trace.status=not_configured`。

`demo_fixture` 永遠不呼叫外部 LLM。

AI 層執行失敗時，不會使官方財報 ingestion 整體失敗；錯誤會進 log 與 limitation，原始官方資料與 historical analysis 仍保存。

## 7. Persistence 與 Monitoring

`FrontendAnalysisSnapshot` schema 已升級到 `1.1.0` 並新增 `ai_analysis`。

因此 Scheduler 背景分析完成後，既有 endpoint：

`GET /api/v1/financial/companies/2454/analysis/latest`

即可讀到：

- `ai_analysis.features`
- `ai_analysis.dimension_assessments`
- `ai_analysis.rule_monitoring`
- `ai_analysis.deterministic_summary`
- `ai_analysis.llm_narrative`
- `ai_analysis.llm_trace`

每條 monitored rule 至少包含：

- `rule_id`
- `rule_scope`
- `rule_version`
- `dimension`
- `assessment_type`
- `severity`
- `evaluation_status`
- `triggered`
- `logic_expression`
- `threshold_basis`
- `evidence_basis`
- `evidence_references`
- `direct_metrics`
- `indirect_metrics`
- `required_features`
- `missing_features`
- `actual_values`

這些欄位可直接做後台 rule monitoring 與老師 meeting 的 Swagger 截圖。

## 8. 驗證策略

單元／整合測試覆蓋：

- common / semiconductor / ic_design 三層規則數量與 provenance。
- R&D intensity 單獨下降但 R&D expense 仍成長時，不得誤觸發 `IC_RD_002`。
- 高壓情境會觸發多因素 high-attention rules。
- COGS / Accounts Receivable XBRL extension mapping。
- Inventory / Receivable turnover days 計算。
- Demo scheduler-style pipeline 會自動建立並 persistence `ai_analysis`。
- LLM mock response parsing 與 trace。

另外 `MOPS iXBRL Smoke` workflow 新增 `smoke_mediatek_ai.py`：實際抓取聯發科 2022–2024 三年官方年度 iXBRL，要求至少能形成核心 metrics、24 layered rules 與 8 dimensions；新 turnover 欄位若來源 taxonomy 缺失會在輸出中明確呈現 coverage，而不是假造數值。

## 9. 目前仍需保留的研究限制

- AI v2 完整 layered catalog 目前只支援 IC 設計；晶圓代工與封裝測試仍沿用既有 historical subindustry engine。
- 年度 Q4 資料適合 3–5 年趨勢，但 inventory / AR turnover 的即時性仍不如季度資料；未來應加入 quarterly analysis。
- heuristic 門檻尚待 peer baseline 實證校準。
- LLM 只整合結構化 evidence，不負責產生官方數字或修改 deterministic rule verdict。
- 本系統是財報證據與基本面風險分析，不提供投資建議或股價預測。
