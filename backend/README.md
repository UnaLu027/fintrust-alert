# Financial Evidence Backend MVP

半導體產業的財務主張抽取與官方財報量化查證服務。

## 已完成

- 半導體公司 registry（保留子產業，不把系統鎖死為台積電或晶圓代工）
- 中文財務數值主張抽取
- 明確年度／季度期間正規化
- SQLite normalized financial facts repository
- 年增率、季增率、百分點差異、直接數值與方向查證
- supported／partially_supported／contradicted／insufficient_evidence／not_applicable
- 公式、輸入值、來源與限制輸出
- normalized facts ingestion API

## 尚未假裝完成

- MOPS Inline XBRL 自動下載與 taxonomy mapping
- Yahoo 財經／X 實際內容擷取
- 訓練後的 claimability classifier
- 歷史 3–5 年官方 facts backfill

這些項目未完成時，API 會回傳 evidence insufficient，而不會由模型猜測數值。

## 執行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -q
```

預設 SQLite 路徑是 `./data/financial_facts.sqlite3`，可用 `FINANCIAL_DATABASE_PATH` 修改。
