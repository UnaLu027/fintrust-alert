# FinTrust Alert Financial Rule Engine MVP

半導體產業專用的財報抓取、財務指標計算與版本化規則分析服務。

## 已完成

- 從 TWSE OpenAPI 抓取上市公司最新綜合損益表、資產負債表與月營收
- 依股票代號篩選半導體公司資料
- 中文欄位與民國年／季別正規化
- 毛利率、營業利益率、淨利率、負債比、權益比率、流動比率、存貨占資產比
- 單月營收年增率／月增率重新計算
- 會計恆等式差異與官方營收成長率重算檢查
- 版本化半導體規則設定檔
- positive／normal／attention／high_attention／data_issue／insufficient_data
- 公式、輸入值、門檻、來源與限制輸出
- React 前端「財報規則引擎」頁面

## 主要 API

```text
GET /api/v1/financial/health
GET /api/v1/financial/companies
GET /api/v1/financial/rules
GET /api/v1/financial/statements/2330/analyze
```

`statements/{ticker}/analyze` 的處理流程：

```text
TWSE OpenAPI
  → 公司資料篩選
  → 財報欄位正規化
  → 固定公式重算
  → semiconductor_rules.json
  → 結構化分析結果
```

## 執行後端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -q
```

Windows PowerShell：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -q
```

## 執行前端

```bash
npm install
npm run dev
```

前端預設呼叫 `http://localhost:8000`。部署時設定：

```text
VITE_FINANCIAL_API_BASE_URL=https://你的後端網址
```

後端跨來源設定：

```text
CORS_ALLOW_ORIGINS=https://你的前端網址,http://localhost:5173
```

## 現階段限制

- TWSE OpenAPI 財報端點主要是最新公開快照，不提供任意 3–5 年歷史期間查詢。
- MOPS Inline XBRL 自動下載、taxonomy mapping、歷史回填尚未完成。
- 現金流量表、資本支出、自由現金流與連續多期趨勢規則尚未啟用。
- 規則門檻是可調整的 MVP 預設值，正式研究版需用半導體子產業與公司歷史資料校準。
- 規則結果僅為財務趨勢與風險提示，不構成投資建議。
