# GitHub Codespaces 後端 Demo（不需要 Google Cloud Billing）

本方案執行與 Cloud Run 相同的 FastAPI、財務指標、子產業規則與 repository interface；差異只有持久化後端暫時使用 Codespace 內的 SQLite，而正式環境使用 Firestore。

## 一、建立 Codespace

1. 打開 `UnaLu027/fintrust-alert`。
2. 切換到 `feature/financial-statement-ai-mvp`。
3. 點選 `Code` → `Codespaces` → `Create codespace`。
4. 等待 `.devcontainer/post-create.sh` 自動安裝 Python、Arelle／twmops、Node 與專案依賴。

專案已設定自動轉送 8000（FastAPI）與 5173（Vite）port。

## 二、一鍵啟動後端

在第一個 Terminal 執行：

```bash
bash scripts/codespaces-start-backend.sh
```

腳本會自動：

- 啟用 `backend/.venv`
- 設定 SQLite persistence
- 設定 MOPS iXBRL cache
- 啟動 `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- 嘗試將 Codespaces 8000 port 設為 Public
- 印出 `/docs` 與 health check 網址

若外部無法開啟，請在 Codespaces 的 `PORTS` 面板將 8000 的 Visibility 改為 `Public`。

## 三、先跑官方資料 Demo

另開第二個 Terminal：

```bash
bash scripts/codespaces-run-demo.sh 2330 3 2024 official
```

流程：

```text
TWSE 最新資料
→ MOPS 2022–2024 年度 iXBRL
→ 正規化財務科目
→ 指標計算
→ 晶圓代工規則
→ SQLite persistence
→ latest frontend snapshot
```

執行完成後，腳本會自動顯示六張資料表筆數、最近 analysis run 與最新 snapshot 摘要，並將完整 JSON 存在：

```text
backend/data/demo-output/
```

## 四、外部來源異常時的技術流程備援

TWSE 或 MOPS 若在 meeting 當下限制 Codespaces IP，可使用：

```bash
bash scripts/codespaces-run-demo.sh 2330 3 2024 demo_fixture
```

`demo_fixture` 使用合成且固定的資料，只驗證：

- 欄位正規化
- 指標公式
- 子產業規則 dispatch
- SQLite 寫入
- snapshot 取出

API、summary、source name 與 limitations 都會明確顯示 `DEMO FIXTURE`，不得將其說成官方財報或公司真實數值。正式報告與結論仍使用 `official` 模式。

## 五、FastAPI Swagger Demo

打開腳本印出的：

```text
https://<codespace>-8000.app.github.dev/docs
```

### 執行分析與寫入資料庫

```text
POST /api/v1/financial/admin/companies/{ticker}/refresh
```

建議參數：

```text
ticker = 2330
years = 3
end_year = 2024
trigger = demo
source_mode = official
```

外部來源無法連線時才把 `source_mode` 改為 `demo_fixture`。

### 從資料庫取出前端內容

```text
GET /api/v1/financial/companies/2330/analysis/latest
```

### 查看指標與執行紀錄

```text
GET /api/v1/financial/companies/2330/metrics
GET /api/v1/financial/companies/2330/analysis-runs
```

## 六、直接檢查 SQLite

```bash
cd backend
source .venv/bin/activate
python scripts/inspect_demo_database.py --ticker 2330
```

會檢查：

```text
financial_filings
normalized_financial_facts
calculated_metrics
analysis_runs
rule_results
latest_analysis_snapshots
```

## 七、Meeting 建議展示順序

1. Swagger 執行 `POST .../refresh`。
2. 切到第一個 Terminal，看 `twse_fetch`、`mops_fetch`、`persist` 與 `pipeline_completed` log。
3. 執行 `inspect_demo_database.py`，展示每張資料表的筆數。
4. Swagger 執行 `GET .../analysis/latest`，證明分析結果由資料庫再次取出。
5. 指出正式環境只會把 repository backend 從 SQLite 切為 Firestore，規則與 API 不變。

## 八、與正式部署的差異

| 項目 | Codespaces Demo | 正式部署 |
|---|---|---|
| API runtime | Codespaces | Cloud Run |
| 持久化 | SQLite | Firestore |
| 觸發 | meeting 手動 refresh | Cloud Scheduler |
| 公開網址 | 暫時 `app.github.dev` | `run.app`／`web.app` |
| 核心分析程式 | 相同 | 相同 |

Codespaces 關閉後公開服務會停止，因此它是 meeting 與開發驗證方案，不是正式上線環境。
