# Official Evidence Sources and Semiconductor Rule Basis

本文件整理老師要求的兩件事：

1. 年度財報之外，加入較即時的官方資料：法說會與重大訊息。
2. 半導體子產業規則需要符合產業特性，且有文獻或公開分析資料支撐。

## 官方資料層設計

### Layer 1：年度財報 / MOPS iXBRL

用途：提供可重現的量化證據，包含營收、毛利、營業利益、現金流、資本支出、存貨、負債與流動性等欄位。

限制：年度資料較穩定，但時效性不足；適合作為基準層，不足以解釋近期展望或突發事件。

### Layer 2：法說會 metadata / 文件

公開資訊觀測站導覽列包含「重大訊息查詢公告法說會」等項目，顯示法說會屬於官方揭露資訊的一部分。證交所 WebPro 也將法人說明會分類為影音內容，並說明站外法說會連結擷取自公開資訊觀測站近 3 年資料，連結內容由各申報公司自行負責。多家公司投資人關係頁也將法人說明會查詢導向 MOPS 的 `t100sb07_1` 頁面。

系統用途：

- 抓取法說會日期、標題、簡報或影音連結。
- 後續用 Gemini 摘要近期展望、需求、產能、庫存與資本支出相關敘述。
- 與年度財報指標併列，不讓 LLM 取代財報計算。

目前 Phase 4：metadata MVP，只保存查詢入口與子產業關聯指標，尚未宣稱已完成 PDF / 影音全文解析。

### Layer 3：重大訊息 metadata / 分類

公開資訊觀測站提供重大訊息查詢，常見入口為 `t05st01`。證交所也說明公開資訊觀測站提供上市櫃公司自行輸入的財務、業務及重大資訊，內容包括重大訊息、公司概況、營運概況、財務報表與公告查詢等。

系統用途：

- 先保存公司重大訊息查詢入口。
- 以保守 keyword classifier 做事件分類，例如擴產、庫存、營收、融資、併購、營運中斷、訴訟裁罰。
- 將事件類型對應到財務指標，例如擴產對應資本支出、自由現金流與負債比；庫存需求對應存貨年增率、營收年增率與現金轉換。

目前 Phase 5：metadata / classification MVP，尚未批次抓取所有歷史公告。

## 子產業規則設計基礎

### 晶圓代工

產業特性：高資本密集、高固定資產與設備投資，單看資本支出高不應直接判斷為負面。

規則方向：

- 觀察資本支出強度是否高於公司自身歷史中位數。
- 同時要求自由現金流轉弱與毛利率下降，避免把正常擴產誤判為風險。
- 使用公司自身歷史基準作為 MVP 門檻，後續再導入同子產業 median / MAD。

對應 rule：`FOUNDRY_CAPEX_MARGIN_001`。

### IC 設計

產業特性：相對輕資產，研發投入與產品週期重要；研發費用增加本身不應直接列為正向或負向，必須搭配營收、毛利、庫存與現金轉換看。

規則方向：

- 研發強度變化只作為投入訊號。
- 只有當營收下滑、存貨增速明顯高於營收，且現金轉換偏弱時，才提示研發投入轉化或產品去化壓力。
- AI v2 仍保留 deterministic rule verdict，Gemini 只做語意整合。

對應 rule：`ICDESIGN_RD_INVENTORY_001`。

### 封裝測試

產業特性：同時需要產能投資與營運資金管理；存貨、營業現金流、負債與流動性要一起看。

規則方向：

- 存貨成長若大幅高於營收成長，可能代表去化壓力。
- 若同時營業現金流轉弱、負債比提高，才列為營運資金與資金結構壓力。
- 這符合老師提到「測試封裝要不要進來」的擴充要求。

對應 rule：`PACKAGING_WORKING_CAPITAL_001`。

## 文獻與公開資料支撐

- Wu, H.-Y., Chen, J.-K., Chen, I.-S., & Zhuo, H.-H. (2019). Ranking universities based on performance evaluation by a hybrid MCDM model. *Measurement, 137*, 203–213. DOI: 10.1016/j.measurement.2019.01.053. 先前引用用於台灣半導體研發效率與績效分析基礎。
- Sher, P. J., & Yang, P. Y. (2005). The effects of innovative capabilities and R&D clustering on firm performance: The evidence of Taiwan's semiconductor industry. *Technovation, 25*(1), 33–43. DOI: 10.1016/S0166-4972(03)00068-3.
- Chen, M.-Y., & Wu, H.-Y. (2020). An analysis of the impact of R&D intensity on financial performance. *Sustainability, 12*(12), 5128. DOI: 10.3390/su12125128.
- TWSE 公開資訊觀測站與證交所服務介紹：公開資訊觀測站提供上市櫃公司重大訊息、營運概況、財務報表與公告查詢；WebPro 影音傳播網提供法人說明會與重大訊息記者會等影音內容。

## 對系統設計的約束

- 規則只做風險提示，不做投資建議。
- LLM 不得猜數字、重算會計值或改 deterministic verdict。
- 所有門檻先標示為 MVP heuristic，後續需要用公司歷史與同子產業 peer baseline 校準。
- 法說會與重大訊息目前為 metadata MVP，回傳內容必須清楚標示限制，不能宣稱已完成全文查證。
