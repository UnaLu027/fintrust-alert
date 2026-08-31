# Flask 前端整合指南：FinTrust 財報官方證據層

本文件給 private `Financial-Risk-Alert-System` Flask/Jinja 專案使用。目標是明天整合時不用碰 FastAPI 內部邏輯，只要把 Flask 當 BFF（Backend for Frontend）去呼叫 FinTrust FastAPI。

## 1. 整合定位

- Flask 前端：負責登入、頁面、dashboard、template、按鈕與使用者互動。
- FinTrust FastAPI：負責財報資料、規則結果、官方證據、法說會 / 重大訊息 metadata。
- 瀏覽器不要直接打 FastAPI；瀏覽器打 Flask，Flask server-side 再呼叫 FastAPI。
- API Key / ingestion token 只能放在 Flask server 環境變數，不放到 JS。

## 2. 複製檔案

把本 repo 的下列檔案複製到 private Flask 專案可 import 的位置：

```text
integrations/flask/fintrust_client.py
integrations/flask/financial_routes.py
```

建議放在 private Flask 專案：

```text
services/fintrust_client.py
routes/financial_routes.py
```

若移動路徑，請調整 `financial_routes.py` 裡的 import。

## 3. Flask app 註冊 blueprint

在 private Flask 專案的 `app.py` 或 app factory 加：

```python
from routes.financial_routes import create_financial_blueprint

app.register_blueprint(create_financial_blueprint())
```

設定環境變數：

```bash
export FINTRUST_API_BASE_URL="http://127.0.0.1:8000"
export FINTRUST_INGESTION_TOKEN="本機若沒有設定 INGESTION_API_TOKEN 可以先不填"
```

Codespaces 時，`FINTRUST_API_BASE_URL` 可以用後端 port 8000 的 forwarded URL 或本機同 workspace 的 `http://127.0.0.1:8000`。

## 4. Flask 端提供給前端的 proxy endpoints

註冊 blueprint 後，private 前端可呼叫：

```text
GET  /api/financial/health
GET  /api/financial/companies
GET  /api/financial/companies/<ticker>/card
GET  /api/financial/companies/<ticker>/raw
GET  /api/financial/companies/<ticker>/analysis/latest
GET  /api/financial/companies/<ticker>/official-evidence
GET  /api/financial/companies/<ticker>/conferences
GET  /api/financial/companies/<ticker>/material-events
GET  /api/financial/companies/<ticker>/metrics
GET  /api/financial/companies/<ticker>/analysis-runs
POST /api/financial/admin/companies/<ticker>/refresh
```

最推薦前端 dashboard 先接：

```text
GET /api/financial/companies/2330/card
```

這個 endpoint 會整理成比較好畫卡片的 payload：

```json
{
  "success": true,
  "data": {
    "ticker": "2330",
    "company_name": "台積電",
    "subindustry": "晶圓代工",
    "overall_severity": "normal",
    "summary": "...",
    "key_metrics": [],
    "rule_cards": [],
    "evidence_readiness": "ready_for_frontend_integration",
    "evidence_layers": ["financial_snapshot", "investor_conference", "material_event"],
    "official_sources": [],
    "conference_count": 1,
    "material_event_count": 1,
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
    ]
  }
}
```

## 5. 前端頁面建議欄位

Dashboard card：

- company_name / ticker
- subindustry
- overall_severity
- summary
- key_metrics 前 3–6 個
- triggered rule_cards
- evidence_readiness
- evidence_layers
- limitations 數量

Detail page：

- 全部 key_metrics
- 全部 rule_cards
- official_sources
- investor_conferences
- material_events
- limitations
- raw source links

## 6. Debug 與 fallback 原則

整合時不要讓頁面因單一來源失敗整頁壞掉。

- `snapshot` 成功、`conferences` 失敗：仍顯示財報規則卡，法說會區塊顯示「官方來源抓取受限」。
- `official_evidence` 成功但 conference 是 metadata_only：詳細頁顯示 limitation。
- 2330 / 2303 若遇到 403：標示為官方來源阻擋，不當作系統錯誤。
- refresh 按鈕只能放在後台 / admin；一般使用者頁面只讀取 latest snapshot。

## 7. 明天整合的最短路徑

1. 啟動 FinTrust FastAPI：

```bash
cd /workspaces/fintrust-alert
bash scripts/codespaces-start-backend.sh
```

2. Flask 專案設定：

```bash
export FINTRUST_API_BASE_URL="http://127.0.0.1:8000"
```

3. private Flask 註冊 blueprint。

4. 前端先接 `GET /api/financial/companies/2330/card`。

5. 页面穩定後再接 refresh/admin、official-evidence raw detail。

## 8. 尚未完成但已保留接口

- PDF / presentation / transcript 文字抽取。
- Gemini official evidence summary。
- MOPS 法說會 POST/session 更精準解析。
- 2330 / 2303 official IR 403 的長期處理：改用官方可下載文件 URL、手動 source registry、或 browser/session-based fetch。
