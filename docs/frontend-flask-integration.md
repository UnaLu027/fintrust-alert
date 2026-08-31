# Flask 前端整合指南：FinTrust 財報官方證據層

本文件給 private `Financial-Risk-Alert-System` Flask/Jinja 專案使用。目標是明天整合時不用碰 FastAPI 內部邏輯，只要把 Flask 當 BFF（Backend for Frontend）去呼叫 FinTrust FastAPI。

我目前看到 zip 結構是單一 Flask app：`app.py`、`static/script.js`、`static/style.css`、`templates/*.html`。因此最短整合方式是先把 proxy blueprint 註冊進現有 `app.py`，再讓 `static/script.js` 呼叫 `/api/financial/companies/<ticker>/card`。

## 1. 整合定位

- Flask 前端：負責登入、頁面、dashboard、template、按鈕與使用者互動。
- FinTrust FastAPI：負責財報資料、規則結果、官方證據、法說會 / 重大訊息 metadata、官方文件抽取。
- 瀏覽器不要直接打 FastAPI；瀏覽器打 Flask，Flask server-side 再呼叫 FastAPI。
- API Key / ingestion token 只能放在 Flask server 環境變數，不放到 JS。

## 2. 複製檔案

把本 repo 的下列檔案複製到 private Flask 專案可 import 的位置：

```text
integrations/flask/fintrust_client.py
integrations/flask/financial_routes.py
```

對目前 zip 最少改動的放法：

```text
Financial-Risk-Alert-System-main/
├── app.py
├── fintrust_client.py       # 新增
├── financial_routes.py      # 新增
├── static/
└── templates/
```

若放到 `services/` 或 `routes/`，請調整 `financial_routes.py` 裡的 import。

## 3. Flask app 註冊 blueprint

在 private Flask 專案的 `app.py` 加：

```python
from financial_routes import create_financial_blueprint

app.register_blueprint(create_financial_blueprint())
```

設定環境變數：

```bash
export FINTRUST_API_BASE_URL="http://127.0.0.1:8000"
export FINTRUST_INGESTION_TOKEN="本機若沒有設定 INGESTION_API_TOKEN 可以先不填"
```

Codespaces 時，`FINTRUST_API_BASE_URL` 可以用後端 port 8000 的 forwarded URL 或同 workspace 的 `http://127.0.0.1:8000`。

## 4. Flask proxy endpoints

註冊 blueprint 後，private 前端可呼叫：

```text
GET  /api/financial/health
GET  /api/financial/companies
GET  /api/financial/companies/<ticker>/card
GET  /api/financial/companies/<ticker>/raw
GET  /api/financial/companies/<ticker>/analysis/latest
GET  /api/financial/companies/<ticker>/official-evidence
GET  /api/financial/companies/<ticker>/official-evidence-card
GET  /api/financial/companies/<ticker>/conferences
GET  /api/financial/companies/<ticker>/conference-documents
GET  /api/financial/companies/<ticker>/material-events
GET  /api/financial/companies/<ticker>/metrics
GET  /api/financial/companies/<ticker>/analysis-runs
POST /api/financial/official-documents/extract
POST /api/financial/admin/companies/<ticker>/refresh
```

最推薦前端 dashboard 先接：

```text
GET /api/financial/companies/2330/card
```

需要 live 法說會 / 文件抽取時再加 query：

```text
GET /api/financial/companies/2454/card?live=true&extract=true
```

## 5. Card payload 重點

`/card` 會回前端比較好畫的 payload：

```json
{
  "success": true,
  "data": {
    "schema_version": "frontend-official-evidence-card-1.0.0",
    "ticker": "2330",
    "company_name": "台積電",
    "subindustry": "晶圓代工",
    "overall_severity": "normal",
    "headline": "台積電官方證據層已整合...",
    "summary": "...",
    "key_metrics": [],
    "rule_cards": [],
    "investor_conferences": [],
    "material_events": [],
    "disclosure_claims": [],
    "source_status": {
      "financial_snapshot_present": true,
      "conference_count": 1,
      "document_link_count": 0,
      "text_preview_count": 0,
      "claim_count": 0
    },
    "limitations": [],
    "errors": []
  }
}
```

若部分來源失敗，HTTP 可能是 `207`，但 payload 仍可畫頁面：

```json
{
  "success": false,
  "data": {
    "errors": [
      {"layer": "conferences", "message": "...", "status_code": 502}
    ],
    "limitations": ["官方來源抓取受限，但財報 snapshot 仍可顯示。"]
  }
}
```

## 6. 前端頁面建議欄位

Dashboard card：

- company_name / ticker
- subindustry
- overall_severity
- headline / summary
- key_metrics 前 3–6 個
- triggered rule_cards
- evidence_readiness
- source_status.document_link_count / claim_count
- limitations 數量

Detail page：

- 全部 key_metrics
- 全部 rule_cards
- official sources
- investor_conferences
- conference document_extractions
- material_events
- disclosure_claims
- limitations
- raw source links

## 7. Debug 與 fallback 原則

整合時不要讓頁面因單一來源失敗整頁壞掉。

- `snapshot` 成功、`conferences` 失敗：仍顯示財報規則卡，法說會區塊顯示「官方來源抓取受限」。
- `official_evidence` 成功但 conference 是 metadata_only：詳細頁顯示 limitation。
- 2330 / 2303 若遇到 403：標示為官方來源阻擋，不當作系統錯誤。
- document extraction 若遇到 403 / download failed：顯示 official link 與 status，不移除整筆 evidence。
- refresh 按鈕只能放在後台 / admin；一般使用者頁面只讀取 latest snapshot。

## 8. 目前 zip 的最小 JS 串接範例

可先在 `static/script.js` 的 summary page 區塊中加入：

```javascript
fetch('/api/financial/companies/2330/card')
  .then(r => r.json())
  .then(payload => {
    const data = payload.data || {};
    console.log('FinTrust card', data);
    // 先把 data.headline / data.summary / data.key_metrics 接到 summary.html
  });
```

等卡片可以顯示後，再把 ticker 從使用者輸入或欄位搜尋中抽出。

## 9. 本 repo 驗證指令

```bash
cd /workspaces/fintrust-alert
git pull --ff-only origin feature/financial-statement-ai-mvp
bash scripts/codespaces-start-backend.sh
```

另一個 terminal：

```bash
npm run demo:official
npm run demo:official-evidence
npm run demo:conferences:extract
```

可測 API：

```bash
curl 'http://127.0.0.1:8000/api/v1/financial/companies/2330/official-evidence-card'
curl 'http://127.0.0.1:8000/api/v1/financial/companies/2454/official-evidence-card?fetch_conference_live=true&extract_documents=true'
```

## 10. 後續仍需補強

- Gemini official evidence summary：目前先保留 bounded input/output schema，下一步可接 Gemini，但不能覆蓋 deterministic verdict。
- MOPS 法說會 POST/session 更精準解析：目前已有 debug 檔，不再讓整個 Phase 4 卡住。
- 2330 / 2303 official IR 403：長期可改用官方可下載文件 URL、手動 source registry、或 browser/session-based fetch。
