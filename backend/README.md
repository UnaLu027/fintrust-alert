# FinTrust Alert Financial Rule Engine MVP

半導體產業專用的官方財報抓取、財務指標計算與版本化規則分析服務。

## 已完成

### TWSE 最新快照

- 從 TWSE OpenAPI 抓取上市公司最新綜合損益表、資產負債表與月營收
- 依股票代號篩選半導體公司資料
- 中文欄位與民國年／季別正規化
- 毛利率、營業利益率、淨利率、負債比、權益比率、流動比率、存貨占資產比
- 單月營收年增率／月增率重新計算
- 會計恆等式差異與官方營收成長率重算檢查

### MOPS Inline XBRL 歷史層

- 自動下載 MOPS 第 4 季／年度合併 iXBRL
- 使用 Arelle 解析 taxonomy、facts、labels 與 contexts
- 依 current-year context 選值，排除同一文件內的前期比較數
- 支援近 3、4 或 5 個完整年度
- 正規化營收、毛利、營業利益、淨利、EPS、資產、負債、權益、存貨、營業現金流、資本支出與研發費用
- 計算營收年增率、毛利率、營業利益率、淨利率、存貨年增率、現金轉換比、自由現金流、資本支出強度、研發強度、負債比與流動比率
- 公司自身歷史複合規則：連續營收衰退、毛利率下滑、存貨成長高於營收、獲利與現金流背離、負自由現金流、資本支出壓力、負債比變化與研發趨勢
- 下載或 taxonomy mapping 失敗時保留 error／missing，不以零值補齊

### 可解釋規則輸出

- 規則存放於版本化 JSON 設定檔
- positive／normal／attention／high_attention／data_issue／insufficient_data
- 輸出公式、數值、門檻、年度、官方來源與資料限制
- React 前端「財報規則引擎」同時提供最新快照與 3–5 年歷史分析

## 主要 API

```text
GET /api/v1/financial/health
GET /api/v1/financial/companies
GET /api/v1/financial/rules
GET /api/v1/financial/statements/2330/analyze
GET /api/v1/financial/statements/2330/history?years=5
```

### 最新快照流程

```text
TWSE OpenAPI
  → 公司資料篩選
  → 財報欄位正規化
  → 固定公式重算
  → semiconductor_rules.json
  → 結構化分析結果
```

### 歷史財報流程

```text
MOPS consolidated annual iXBRL
  → Arelle 解析 facts／contexts／labels
  → 選取當年度 annual／instant context
  → taxonomy alias mapping
  → 3–5 年趨勢指標
  → semiconductor_historical_rules.json
  → 結構化歷史分析結果
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

## 不需要使用者手動處理的項目

- 不需要自行下載財報
- 不需要上傳 PDF、Excel 或 XBRL
- 不需要手動輸入財務數字
- 選擇公司及歷史年數後，由後端向 TWSE／MOPS 取得資料並分析

## 部署時可能需要的一次性操作

1. 部署 `backend/` FastAPI 服務。
2. 在前端設定 `VITE_FINANCIAL_API_BASE_URL`。
3. 在後端設定 `CORS_ALLOW_ORIGINS`。
4. 若部署平台對 MOPS 無法連線，需更換可連線的後端區域或主機；程式不會要求使用者改用手動上傳。

## 現階段限制

- 第一版歷史層只使用年度 Q4 合併財報，避免把 Q2／Q3 累計值誤當成單季。
- 公司自訂 taxonomy concept 可能需要逐公司補充 alias；無法確認期間或概念時回傳資料不足。
- 尚未完成財報重編版本追蹤、季度累計轉單季與同子產業中位數／MAD 基準。
- 規則門檻是可調整的 MVP 預設值，正式研究版需用半導體子產業與公司歷史資料校準。
- 規則結果僅為財務趨勢與風險提示，不構成投資建議。
