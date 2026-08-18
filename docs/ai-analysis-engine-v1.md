# AI 財報分析引擎 v1

## 目的

本模組不是把財報整份交給 LLM 自由解讀，而是建立可追溯的 hybrid AI 分析流程：

1. MOPS／XBRL 官方財報形成歷史財務指標。
2. Feature Engine 建立直接指標、間接指標與跨指標差距。
3. Monitorable Rule Engine 以設定檔執行 IF–THEN 分析。
4. 八個分析面向分別形成 assessment。
5. LLM 只接收結構化 evidence 與規則結果，負責跨面向整合與一般使用者說明。
6. 每一條規則、使用欄位、實際值、觸發狀態與 LLM trace 都保留，方便後台監控與簡報展示。

## 八大分析面向

| Dimension | 中文 | 主要目的 |
|---|---|---|
| growth | 成長性 | 不只看營收，交叉營業利益、淨利與 EPS |
| profitability | 獲利能力 | 毛利率、營業利益率、淨利率及其變化 |
| rd_innovation | 研發與創新 | IC 設計研發投入及其產業脈絡 |
| operating_efficiency | 營運效率 | 存貨與營收去化關係 |
| cash_flow | 現金流品質 | OCF、FCF 與現金轉換能力 |
| financial_structure | 財務結構 | 負債、流動性與現金緩衝 |
| earnings_quality | 盈餘品質 | 帳面獲利與營業現金流是否同步 |
| investment_efficiency | 投入轉化效率 | 研發投入是否有營收、毛利與現金流的間接支持 |

## Rule 類型

每條規則會標示 `assessment_type`：

- `direct`：直接用該面向核心財務指標衡量。
- `indirect`：以其他財務結果驗證核心指標是否具有品質或轉化效果。
- `cross_factor`：同時使用多個面向的條件判斷。
- `trend`：以跨年度變化而非單一水準判斷。

v1 的 IC 設計 rule catalog 共 24 條，平均每一個分析面向 3 條，後續可以透過同一 JSON schema 擴充，不需要每新增一條規則就重寫 endpoint。

## 可監控欄位

`rule_monitoring` 每一筆至少包含：

- `rule_id`
- `name`
- `dimension`
- `assessment_type`
- `severity`
- `evaluation_status`
- `triggered`
- `logic_expression`
- `direct_metrics`
- `indirect_metrics`
- `required_features`
- `missing_features`
- `actual_values`
- `rationale`

因此後台未來可以直接以這份資料做規則監控頁，不需要重新解析自然語言說明。

## LLM 邊界

LLM 不負責：

- 猜官方數字
- 自行計算財務比率
- 修改 IF–THEN 規則結果
- 預測股價
- 提供買賣建議

LLM 負責：

- 將八個 dimension assessment 做跨面向整合
- 解釋直接證據與間接證據是否一致
- 指出 mixed signals
- 把結果轉成一般使用者可以理解的文字

LLM 透過環境變數設定：

- `FINANCIAL_LLM_ENDPOINT`：完整的 chat-completions-compatible endpoint
- `FINANCIAL_LLM_API_KEY`
- `FINANCIAL_LLM_MODEL`

沒有設定 LLM 時，deterministic 分析仍會完整回傳，`llm_trace.status` 會標記為 `not_configured`。

## Demo / Swagger API

### 1. AI Engine 狀態

`GET /api/v1/financial/ai/health`

適合截圖：

- engine version
- rule version
- rule count
- dimensions
- LLM configured / model
- monitorable_rules

### 2. 規則監控總覽

`GET /api/v1/financial/ai/rules`

適合截圖：

- 24 條規則數量
- direct / indirect / cross_factor / trend
- `logic_expression`
- direct / indirect metrics

### 3. 聯發科 AI 財報分析

`POST /api/v1/financial/ai/companies/2454/analyze?years=3&use_llm=true`

輸出重點：

- `features`：財務與衍生特徵
- `dimension_assessments`：八面向結果
- `rule_monitoring`：每條規則的實際執行情形
- `deterministic_summary`：規則層摘要
- `llm_narrative`：LLM 跨面向整合說明
- `llm_trace`：模型、prompt version、latency、使用的 rule IDs、錯誤狀態

## v1 技術定位

這一版先把「分析引擎」建立成可擴張的 AI infrastructure，而不是宣稱已經能完全取代專業分析師。下一輪可繼續增加：

- 更多 IC 設計指標與 rules
- 季度資料與更細緻趨勢
- peer baseline / 同子產業分布
- rule versioning 與後台 CRUD
- AI claim / 新聞敘事與公司 fundamental profile 的一致性分析
