# 半導體財報查證 MVP：研究基礎與技術決策

本文件記錄第一階段 paper review 對系統設計的直接影響，避免只把論文列成參考資料而沒有落實到架構。

## 1. 文獻整理

### FinQA

Chen et al. (2021) 將財務報告中的文字、表格與數值推理結合，並為答案標註可執行的 gold reasoning programs。這表示財務查證不應只輸出自然語言結論，而要保存可重現的計算步驟。

對 MVP 的影響：

- 每個量化結果保存公式與輸入值。
- 將語言模型限制在主張抽取與證據選擇；算術由程式執行。
- 評估時分開衡量主張抽取正確率與公式執行正確率。

### TAT-QA

Zhu et al. (2021) 指出財務問題通常同時依賴表格與文字，並以 evidence tagging 加上 symbolic aggregation 解題。

對 MVP 的影響：

- 官方證據資料結構同時保留財報數值、欄位名稱及期間脈絡。
- 主張驗證先選出相關欄位與期間，再執行加減乘除、比較或排序。
- 不把整張財報直接塞給模型後要求它自行回答。

### FinDVer

Zhao et al. (2024) 專門研究長篇、混合文字與表格金融文件的可解釋 claim verification，並顯示現有 LLM 即使在 RAG 設定下仍明顯落後人類專家。

對 MVP 的影響：

- 查證流程必須允許「證據不足」，不能強迫模型二選一。
- 結果顯示 evidence attribution、資料期間及原始來源。
- 長文件檢索與最終判定分開測試。

### Numerical Claim Detection in Finance

Shah et al. (2024) 建立金融數值主張偵測資料集，說明在進入計算前，先辨識哪些句子真正包含可驗證的 numerical claim 是獨立且必要的任務。

對 MVP 的影響：

- Pipeline 第一關是 claimability classifier。
- 沒有公司、指標、期間或可檢驗方向的句子回傳 not_applicable 或 insufficient_evidence。
- 未來可使用 weak supervision：由財務關鍵詞、數值格式、期間詞與比較詞產生初始標籤。

### TabVer

Aly 與 Vlachos（2024）將 natural logic 與確定性算術證明整合到表格事實驗證。

對 MVP 的影響：

- 最終 verdict 必須可追溯到數值關係，而不是不可解釋的單一分類分數。
- 將「增加／減少／高於／低於／約為」正規化為可執行比較運算。
- 把百分比變化與百分點變化分成不同操作，避免常見語意錯誤。

### ClaimVer

Dammu et al. (2024) 強調 claim-level verification、細粒度 evidence attribution 與使用者可理解的解釋。

對 MVP 的影響：

- 一篇新聞若含多個主張，應逐一查證，而非對整篇文章只給一個真假標籤。
- 前端標示原句、抽取欄位、支持證據及衝突位置。
- 總體可信度風險由多個主張結果彙整，但保留各主張明細。

### FEVEROUS／混合證據研究

FEVEROUS 及後續 structured evidence extraction、dual-channel evidence fusion 工作顯示，文字與表格證據應保留原始結構並在後段融合，而不是一開始就全部轉成單一文字格式。

對 MVP 的影響：

- X／Yahoo 以文字 evidence 儲存。
- MOPS／XBRL 以結構化 cells 與 statement context 儲存。
- Evidence fusion 只負責整合 verdict，不破壞原始證據格式。

## 2. 最終採用的 MVP 方法

第一階段不訓練大型端到端真假分類器，而採可解釋的 hybrid pipeline：

1. 規則＋輕量 NLP 偵測可量化財務主張。
2. 將主張轉成固定 JSON schema。
3. 依公司、指標與期間檢索官方財報欄位。
4. 以 deterministic functions 計算結果。
5. 依容許誤差輸出 supported、partially_supported、contradicted、insufficient_evidence 或 not_applicable。
6. 將公式、數值、期間、來源與限制一併回傳前端。

此方法符合專題「一種主要查證方法、一個主要模型、先縮小功能」的要求，也較容易展示 explainability。

## 3. 第一階段評估指標

### 主張抽取

- Claim detection precision／recall／F1
- 公司辨識 accuracy
- 指標辨識 accuracy
- 期間解析 exact match
- 數值與單位抽取 exact match

### 證據檢索

- 正確報表命中率
- 正確欄位 recall@k
- 正確期間命中率

### 數值查證

- Program／formula accuracy
- Execution accuracy
- Verdict macro-F1
- Unsupported／insufficient evidence recall

### 可解釋性

- 公式是否可重現
- 來源連結完整率
- 使用者是否能指出判定所依據的數值與期間

## 4. 官方資料策略

- TWSE OpenAPI：適合取得上市公司最新綜合損益表、資產負債表與月營收快照。
- 公開資訊觀測站／Inline XBRL：作為近 3–5 年歷史財報的主要來源。
- 系統資料庫需保留原始 taxonomy concept、中文標籤、期間、合併／個體別、單位與來源 URL。
- 最新快照與歷史 XBRL 的 coverage 要分開標示，不能以最新資料假裝已驗證多年趨勢。

## 5. 參考文獻

Aly, R., & Vlachos, A. (2024). TabVer: Tabular fact verification with natural logic. *Transactions of the Association for Computational Linguistics, 12*, 1648–1671. https://doi.org/10.1162/tacl_a_00722

Chen, Z., Chen, W., Smiley, C., Shah, S., Borova, I., Langdon, D., Moussa, R., Beane, M., Huang, T.-H., Routledge, B., & Wang, W. Y. (2021). FinQA: A dataset of numerical reasoning over financial data. In *Proceedings of EMNLP 2021* (pp. 3697–3711). https://doi.org/10.18653/v1/2021.emnlp-main.300

Dammu, P. P. S., Naidu, H., Dewan, M., Kim, Y., Roosta, T., Chadha, A., & Shah, C. (2024). ClaimVer: Explainable claim-level verification and evidence attribution of text through knowledge graphs. In *Findings of EMNLP 2024* (pp. 13613–13627). https://doi.org/10.18653/v1/2024.findings-emnlp.795

Hu, N., Wu, Z., Lai, Y., Liu, X., & Feng, Y. (2022). Dual-channel evidence fusion for fact verification over texts and tables. In *Proceedings of NAACL 2022* (pp. 5232–5242). https://doi.org/10.18653/v1/2022.naacl-main.384

Shah, A., Hiray, A., Shah, P., Banerjee, A., Singh, A., Eidnani, D. D., Chava, S., Chaudhury, B., & Chava, S. (2024). Numerical claim detection in finance: A new financial dataset, weak-supervision model, and market analysis. In *Proceedings of the Seventh FEVER Workshop* (pp. 170–185). https://doi.org/10.18653/v1/2024.fever-1.21

Zhao, Y., Long, Y., Jiang, T., Wang, C., Chen, W., Liu, H., Tang, X., Zhang, Y., Zhao, C., & Cohan, A. (2024). FinDVer: Explainable claim verification over long and hybrid-content financial documents. In *Proceedings of EMNLP 2024* (pp. 14739–14752). https://doi.org/10.18653/v1/2024.emnlp-main.818

Zhu, F., Lei, W., Huang, Y., Wang, C., Zhang, S., Lv, J., Feng, F., & Chua, T.-S. (2021). TAT-QA: A question answering benchmark on a hybrid of tabular and textual content in finance. In *Proceedings of ACL-IJCNLP 2021* (pp. 3277–3287). https://doi.org/10.18653/v1/2021.acl-long.254
