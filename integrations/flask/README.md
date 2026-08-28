# Flask Integration Adapter

這個資料夾是給共享 `Financial-Risk-Alert-System` Flask 專案使用的整合包。它的目的不是取代 `fintrust-alert` FastAPI，而是讓共享 Flask 介面可以透過 proxy API 讀取財報分析結果。

## 為什麼這樣整合

- Flask：統一使用者介面與搜尋結果頁。
- FastAPI：官方財報資料取得、財報指標計算、規則引擎與 latest snapshot。
- Adapter：讓 Flask 代替瀏覽器呼叫 FastAPI，集中管理 API URL、token 與錯誤處理。

這樣可以回應老師要求的「開始整合、統一介面」，但不需要把兩個不同框架硬合併成一個 `app.py`。

## 複製到共享 Flask 專案

建議放置方式：

```text
Financial-Risk-Alert-System/
  app.py
  services/
    fintrust_client.py
  routes/
    financial_routes.py
  templates/
    _financial_evidence_card.html
  static/
    financial-evidence.js
```

對應複製：

```text
integrations/flask/fintrust_client.py                  -> services/fintrust_client.py
integrations/flask/financial_routes.py                 -> routes/financial_routes.py
integrations/flask/templates/_financial_evidence_card.html -> templates/_financial_evidence_card.html
integrations/flask/static/financial-evidence.js        -> static/financial-evidence.js
integrations/flask/.env.integration.example            -> .env.example or deployment env notes
```

若放到 `services/` 與 `routes/`，請把 `financial_routes.py` 的 import 改成：

```python
from services.fintrust_client import FinTrustClient, FinTrustClientError
```

## 在 Flask app.py 註冊 Blueprint

```python
from routes.financial_routes import create_financial_blueprint

app.register_blueprint(create_financial_blueprint())
```

## 在 summary.html 加入財報證據卡

```jinja2
{% include "_financial_evidence_card.html" %}
<script src="{{ url_for('static', filename='financial-evidence.js') }}"></script>
```

## 環境變數

本機開發：

```env
FINTRUST_API_BASE_URL=http://127.0.0.1:8000
FINTRUST_INGESTION_TOKEN=
```

正式部署：

```env
FINTRUST_API_BASE_URL=https://<cloud-run-fintrust-api-url>
FINTRUST_INGESTION_TOKEN=<server-side-secret>
```

## 第一階段整合目標

1. 在共享前端顯示「官方財報證據」。
2. 先接 `analysis/latest`，展示公司、子產業、整體狀態、摘要與關鍵指標。
3. 後續再接 `analysis-runs` 到分析紀錄頁。
4. 管理端才允許觸發 `refresh`，一般使用者只讀取快照。

## 後續擴充

老師要求的資料即時性可逐步加入：

- 法說會 metadata / 文件摘要
- 重大訊息 metadata / 事件分類
- `official-evidence` aggregate API

共享前端最終只需要接一個官方證據包，不必自行整合年度財報、法說會與重大訊息。
