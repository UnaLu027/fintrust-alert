# 資料庫 Schema — FinTrust Alert

## 概觀

本系統圍繞一條非同步資料管線設計：

```
爬蟲／API 擷取 → raw_items → analysis_jobs（交給 Python 模型） → analyses
   ↳ risk_reasons
   ↳ source_comparisons
   ↳ push_alerts（依使用者 watchlist 比對後 fan-out）
```

- 爬蟲／擷取程式（X 爬蟲、Yahoo 財經新聞、公開資訊觀測站 MOPS）只負責寫入 `raw_items`，不直接產生風險判斷。
- 一筆或多筆 `raw_items` 會被組成一個 `analysis_jobs` 任務，交給 Python 真偽判斷模型服務處理。
- 模型服務完成後寫回 `analyses`、`risk_reasons`、`source_comparisons`，並將 job 標記為完成。
- 系統再依使用者的 `watchlist_items` / `alert_type_preferences` 進行比對，決定是否要產生 `push_alerts`。
- 使用者主動查證（快速查證頁）會直接建立 `analysis_history` 紀錄，指向對應的 `analyses`。

型別對應：本文件的欄位設計對齊前端 `src/types/*.ts` 中的 `RiskLevel`、`VerificationStatus`、`SourceType`、`RiskReasonCode` 等 enum，避免前後端定義漂移。

---

## Entities

### `users`

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| email | varchar, unique | |
| password_hash | varchar | |
| investment_experience | enum(beginner, experienced, news_only) | |
| alert_frequency | enum(realtime, daily_digest, high_risk_only) | |
| created_at | timestamptz | |

### `watchlist_items`

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| user_id | uuid (FK → users) | |
| type | enum(company, industry, keyword) | |
| value | varchar | 例如「台積電」「2330」「AI」「財報」 |
| ticker | varchar, nullable | 若 type=company 且有對應代號 |

### `alert_type_preferences`

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| user_id | uuid (FK → users) | |
| alert_type | enum(suspected_false, pending_verification, source_inconsistent, official_update) | |

### `sources`

設定表，非每次爬蟲都寫入，僅記錄資料來源設定。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| type | enum(x, yahoo, mops) | |
| display_name | varchar | |
| base_url | varchar | |

### `raw_items`

爬蟲／擷取程式寫入的原始資料，尚未經過模型判斷。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| source_id | uuid (FK → sources) | |
| external_id | varchar | 來源平台的原始 ID（貼文 ID、新聞 ID、公告編號） |
| url | varchar | |
| raw_title | text | |
| raw_text | text | |
| author_or_outlet | varchar | 帳號或媒體名稱 |
| published_at | timestamptz | |
| ingested_at | timestamptz | |
| ingestion_batch_id | uuid | 同一批次擷取的分組識別 |

索引：`unique(source_id, external_id)` 避免重複擷取同一筆。

### `analysis_jobs`

代表一次「送交 Python 模型分析」的非同步任務。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| raw_item_id | uuid (FK → raw_items, nullable) | 若由爬蟲觸發 |
| query_source | enum(crawler, user_query), default crawler | 區分自動擷取或使用者快速查證觸發 |
| requested_analysis_types | jsonb | 對應 `AnalysisType[]` |
| status | enum(queued, running, done, failed) | |
| created_at | timestamptz | |
| completed_at | timestamptz, nullable | |

### `analyses`

模型判斷＋多來源比對後的結果，對應前端 `AnalysisResult`。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| analysis_job_id | uuid (FK → analysis_jobs) | |
| title | text | |
| classification | enum(pending, inconsistent, official_confirmed, suspected_false) | 對應 `VerificationStatus` |
| related_ticker | varchar, nullable | |
| related_company | varchar, nullable | |
| risk_level | enum(low, medium, high) | |
| risk_score | smallint | 0–100，僅供內部與後台使用，前端一律轉換為定性文字呈現 |
| verification_status | enum(pending, inconsistent, official_confirmed, suspected_false) | |
| has_official_support | boolean | |
| model_judgment_summary | text | 「模型輔助判斷結果」呈現文字，避免絕對用語 |
| risk_explanation_text | text | 依 risk_level 產生的說明段落 |
| analyzed_at | timestamptz | |

### `risk_reasons`

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| analysis_id | uuid (FK → analyses) | |
| code | enum(exaggerated_tone, insufficient_official_support, source_inconsistency, abnormal_social_spread, investment_inducement_risk, incomplete_information) | |
| label | varchar | |
| explanation | text | |

### `source_comparisons`

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| analysis_id | uuid (FK → analyses) | |
| source_id | uuid (FK → sources) | |
| raw_item_id | uuid (FK → raw_items, nullable) | 對應到的原始資料，若該來源無內容則為 null |
| has_content | boolean | false 代表「暫無官方佐證／尚無報導」狀態 |
| relation_to_original | enum(supports, inconsistent, partially_related), nullable | 主要用於 yahoo |
| model_judgment | text | |
| status_tag | enum(official_confirmed, supportable, no_official_support, pending) | |
| disclaimer_text | text | |

### `push_alerts`

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| user_id | uuid (FK → users) | |
| analysis_id | uuid (FK → analyses) | |
| template_type | enum(credibility_risk, pending_verification, source_inconsistent, official_update, personalized_digest) | |
| title | text | |
| related_target | varchar | |
| risk_level | enum(low, medium, high) | |
| verification_status | enum(pending, inconsistent, official_confirmed, suspected_false) | |
| reason | text | 推播原因 |
| message | text | 完整推播內容，結尾固定附上免責句 |
| created_at | timestamptz | |
| dedup_key | varchar, unique | `user_id + analysis_id + template_type` 組成，避免同一事件重複推播 |

### `analysis_history`

使用者「我查過的」紀錄，與全域 `analyses` 分開，因為同一 `analysis` 可能被多個使用者各自查詢/追蹤。

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | uuid (PK) | |
| user_id | uuid (FK → users) | |
| analysis_id | uuid (FK → analyses) | |
| query_content | varchar | 使用者輸入的查詢內容 |
| is_tracked | boolean | 是否已加入追蹤 |
| analyzed_at | timestamptz | |

---

## 關聯總覽

- `users` 1—N `watchlist_items`
- `users` 1—N `alert_type_preferences`
- `users` 1—N `analysis_history`
- `raw_items` N—1 `sources`
- `raw_items` 1—N `analysis_jobs`（一筆原始資料可能被重新分析）
- `analysis_jobs` 1—1 `analyses`
- `analyses` 1—N `risk_reasons`
- `analyses` 1—N `source_comparisons`（固定對應 x / yahoo / mops 三個來源）
- `analyses` 1—N `push_alerts`（依符合條件的使用者 fan-out）
- `analyses` 1—N `analysis_history`（多位使用者可查詢到同一分析）

## 索引建議

- `users.email` unique
- `raw_items(source_id, external_id)` unique
- `push_alerts.dedup_key` unique
- `analyses(risk_level, analyzed_at)` — 供 dashboard 「今日高風險資訊」查詢
- `analysis_history(user_id, analyzed_at)` — 供分析紀錄頁排序

## 推播 fan-out 規則（對應 `push_alerts` 產生邏輯）

一筆 `analyses` 完成後，系統會比對所有使用者的 `watchlist_items`／`alert_type_preferences`，符合以下條件才會建立對應的 `push_alerts`：

1. `analyses.related_company` / `related_ticker` 命中該使用者的 `watchlist_items`
2. `risk_level` 為 medium/high，或 `verification_status` 剛轉為 `official_confirmed` / `inconsistent`
3. 該 `user_id + analysis_id + template_type` 尚未存在（`dedup_key` 防止重複推播）
