# Phase 4–5 Official Evidence MVP

本文件記錄目前已完成的官方資料擴充：法說會 metadata、重大訊息 metadata / classification，以及 official-evidence aggregate API。

## 回應老師要求

老師提醒年度 XBRL 財報屬於較長期的歷史資料，後續應往更即時的官方資訊延伸：先看法說會，再看重大訊息，最後才與新聞或社群內容整合。本階段因此先建立官方事件 metadata 層，避免直接讓新聞或 LLM 成為唯一來源。

## Phase 4：法說會 metadata

已建立：

```http
GET /api/v1/financial/companies/{ticker}/conferences
```

回傳內容包含公司、子產業、MOPS 法說會查詢入口、子產業關聯指標、metadata-only 狀態與限制。此階段尚未宣稱完成 PDF / HTML / 影音逐字稿解析。

## Phase 5：重大訊息 metadata / classification

已建立：

```http
GET /api/v1/financial/companies/{ticker}/material-events
```

回傳內容包含 MOPS 重大訊息查詢入口、保守 keyword 事件分類、是否財務風險相關、關聯財務指標與 metadata-only 限制。正式版會由 scraper 取得公告標題與內文，本階段先用 query / title 參數支援整合測試。

## Phase 6：Official Evidence Aggregate API

已建立：

```http
GET /api/v1/financial/companies/{ticker}/official-evidence
```

此 API 將年度財報 snapshot、法說會 metadata 與重大訊息 metadata 組合成前端可讀的官方證據包，讓共享 Flask 前端不用自行整合多個來源。

## 來源基礎

- MOPS 法說會常見查詢入口：`t100sb07_1`。
- MOPS 重大訊息常見查詢入口：`t05st01`。
- 詳細的資料來源與規則基礎整理在 `docs/official-evidence-sources-and-rules.md`。

## Demo 指令

```bash
npm run demo:official-evidence
```

輸出：

```text
backend/data/demo-output/official-evidence-summary.json
```

## 重要限制

- 法說會與重大訊息目前是 metadata MVP。
- 不宣稱已完成全文查證或 PDF / 影音摘要。
- Gemini 後續只做摘要與語意整合，不負責猜官方數字或改規則結果。
- 年度財報仍是官方量化證據基準，法說會與重大訊息是即時性補充層。
