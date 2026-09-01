# Phase 3 Semiconductor Live Validation

本文件說明 Phase 3 半導體子產業擴充的 live 驗收流程。此階段目標是回應老師建議：不要只停在台積電，需納入半導體其他子產業，尤其是 IC 設計與封裝測試，並讓結果可以接到共享 Flask 統一介面。

## 驗收公司

| Ticker | 公司 | 子產業 | 驗收目的 |
| --- | --- | --- | --- |
| 2330 | 台積電 | 晶圓代工 | 既有 Demo 基準 |
| 2303 | 聯電 | 晶圓代工 | 驗證同子產業 peer 可重用 foundry rules |
| 2454 | 聯發科 | IC 設計 | 驗證 IC design 與 AI v2 deterministic 分析 |
| 3711 | 日月光投控 | 封裝測試 | 回應老師要求納入封裝測試 |

## 執行方式

先啟動 Codespaces backend：

```bash
cd /workspaces/fintrust-alert
npm run demo:backend
```

在第二個 Terminal 執行 Phase 3 smoke：

```bash
cd /workspaces/fintrust-alert
npm run demo:semiconductor
```

此指令會執行：

```bash
cd backend && PYTHONPATH=. .venv/bin/python scripts/smoke_semiconductor_companies.py --years 3 --end-year 2024 --output data/demo-output/phase3-semiconductor-summary.json
```

輸出檔案：

```text
backend/data/demo-output/phase3-semiconductor-summary.json
```

## 嚴格驗收

一般 `demo:semiconductor` 是老師 review 用診斷模式；若部分公司缺 MOPS 欄位，會以 `WARN` 回報並列出 next actions，不會直接中斷。

若要確認所有公司都達到完整三年與 required metrics，可執行：

```bash
npm run demo:semiconductor:strict
```

嚴格模式遇到缺年度或缺 required metrics 會回傳非 0 exit code，適合 mapping 修正後的最終驗收。

## 輸出重點

每家公司會輸出：

- `available_years`：MOPS 年度 iXBRL 可用年度數。
- `periods`：每年解析狀態、找到的欄位數、缺少欄位與 warning。
- `rule_scope_counts`：是否載入正確子產業規則，例如 `foundry`、`ic_design`、`packaging_testing`。
- `metric_coverage`：各子產業 required metrics 是否成功產生。
- `missing_required_metrics`：後續應補 mapping 的指標。
- `insufficient_rule_ids`：資料不足的規則 ID。
- `phase3_readiness`：是否可以作為前端 snapshot demo。
- `next_actions`：下一步修正建議。

## 判讀方式

### PASS

代表所有公司在目前診斷條件下沒有 fatal failure。仍需檢查個別公司的 `phase3_readiness`。

### WARN

代表至少有公司缺欄位、缺年度或解析失敗，但診斷流程完成。此時應先看：

```text
results[].missing_required_metrics
results[].periods[].fields_missing
results[].next_actions
```

通常下一步是補 `robust_mops_inline_xbrl.py` 的 alias 或調整歷史指標計算。

### FAIL

只會在 strict 模式發生。代表 Phase 3 還不能宣稱 live data 完整驗收。

## 與共享 Flask 整合的關係

Phase 3 smoke 不直接修改共享前端。它的作用是先確認每家公司能否穩定產生財報 evidence。當某家公司 `phase3_readiness` 為 `ready_for_frontend_snapshot_demo` 時，即可透過 Phase 1 的 Flask adapter 在共享介面顯示：

```http
GET /api/financial/companies/{ticker}/analysis/latest
```

後續若要讓共享前端支援公司切換，可先把這四家公司放進前端 selector：

```text
2330 台積電
2303 聯電
2454 聯發科
3711 日月光投控
```

## 與 Gemini 的關係

本階段不更換 LLM provider。組內決定使用 Gemini，因此 Phase 3 smoke 只驗證 deterministic 財報特徵與子產業規則。對於 2454 聯發科，AI v2 也以 `use_llm=False` 執行，不呼叫外部 Gemini API，避免 live smoke 因 API key、quota 或 Gemini 上游流量而失敗。

真正需要 Gemini 的摘要整合，應在資料欄位與子產業規則穩定後再做。