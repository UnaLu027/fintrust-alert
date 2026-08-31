# Rule Evidence and LLM Governance

This document explains why the financial rules exist, which evidence supports them, and how Gemini may be used without turning the system into an unexplained investment-advice model.

## Design principle

The system separates three layers:

1. **Official quantitative evidence**: MOPS / TWSE financial filings, iXBRL facts, computed metrics, and deterministic rule results.
2. **Official textual evidence**: investor-conference disclosures and material-event announcements.
3. **LLM interpretation**: Gemini may summarize, connect, and explain the official evidence, but it cannot rewrite financial numbers, change deterministic rule verdicts, or invent missing data.

This keeps the system more intelligent than a keyword matcher while preserving explainability.

## Data coverage

`SEM_HIST_DATA_001` exists because fewer than three comparable annual observations should not be used to form a long-term trend conclusion. This is a data-quality guardrail rather than a risk rule. It prevents the frontend or LLM from presenting a one-year observation as a durable pattern.

## Growth

`SEM_HIST_GROWTH_001` uses two consecutive years of revenue decline. Revenue is a direct output measure in official income statements, but one year can be affected by demand cycles, currency, or one-off product transitions. Requiring two periods preserves enough sensitivity for monitoring while reducing single-year false positives.

## Profitability

`SEM_HIST_PROFIT_001` evaluates gross-margin change in percentage points instead of using a fixed cross-industry level. Gross margin in semiconductor firms reflects product mix, pricing, process technology, yield, and utilization. Using company-specific change is more appropriate than imposing a universal threshold across foundry, IC design, and packaging companies.

## Inventory and working capital

`SEM_HIST_INV_001` compares inventory growth with revenue growth. Inventory alone is not a sufficient signal because inventory can rise during strategic ramp-up, node migration, or customer stocking. A gap between inventory growth and revenue growth is a more conservative indicator of potential demand mismatch or product-cycle pressure.

## Earnings quality

`SEM_HIST_CASH_001` and `SEM_HIST_CASH_002` compare profitability with operating cash flow. The purpose is not to estimate valuation, but to detect whether reported profit is being converted into operating cash. These rules are grounded in basic cash-flow and earnings-quality analysis and use official income-statement / cash-flow-statement fields.

## Free cash flow

`SEM_HIST_FCF_001` treats negative free cash flow as context-dependent. Semiconductor firms may legitimately have negative free cash flow during expansion. The rule therefore distinguishes one-year negative FCF from consecutive negative FCF and does not treat a single year as automatically high risk.

## CapEx

`SEM_HIST_CAPEX_001` and `FOUNDRY_CAPEX_MARGIN_001` use capital expenditure intensity together with free cash flow and margin movement. This reflects the capital-intensive nature of semiconductor manufacturing. High capital expenditure is not negative by itself; it becomes more relevant when it is unusually high relative to company history and appears together with cash-flow or margin pressure.

## Financial structure

`SEM_HIST_STRUCTURE_001` monitors debt ratio by combining an absolute level with the company's own historical change. This is more defensible than applying one fixed cross-industry number because foundry, IC design, and packaging/testing have different asset intensity and capital structures.

## R&D intensity

`SEM_HIST_RD_001` is informational, not a direct risk trigger. Sher and Yang (2005) study innovative capabilities and R&D clustering in Taiwan's semiconductor industry and connect innovation-related capability with firm performance. Chen and Wu (2020) examine R&D intensity and financial performance in Taiwan's semiconductor industry and discuss delayed effects of R&D. Because R&D effects may be deferred, the rule deliberately avoids saying that higher R&D spending is positive or negative by itself.

## Foundry

`FOUNDRY_CAPEX_MARGIN_001` applies to wafer foundries such as 2330 and 2303. It requires a combination of:

- CapEx intensity above the company's historical baseline.
- Negative free cash flow.
- Gross-margin deterioration.

This prevents the system from misclassifying normal capacity expansion as a risk. The rule is a composite operating-pressure signal, not an investment recommendation.

## IC design

`ICDESIGN_RD_INVENTORY_001` applies to 2454. IC design is relatively asset-light compared with foundry manufacturing, so the monitoring emphasis shifts toward:

- R&D intensity.
- Revenue growth.
- Inventory growth relative to revenue.
- Cash conversion.

R&D intensity alone is not a risk. The rule only increases attention when R&D investment is accompanied by revenue decline, inventory/revenue divergence, and weak cash conversion.

## Packaging testing

`PACKAGING_WORKING_CAPITAL_001` applies to OSAT / packaging and testing companies such as 3711. The rule combines:

- Inventory growth relative to revenue.
- Operating cash-flow deterioration.
- Debt-ratio increase.

This reflects the fact that packaging/testing pressure is often visible through working capital, utilization, and funding structure together rather than through one isolated ratio.

## LLM governance

Gemini is allowed to perform bounded intelligence:

- Summarize official filings, investor-conference text, and material-event text.
- Group evidence into themes such as demand, CapEx, inventory, cash flow, R&D, or capital structure.
- Explain why a deterministic rule was triggered or not triggered.
- Identify missing evidence and state limitations.
- Suggest which official evidence should be checked next.

Gemini is not allowed to:

- Change deterministic rule severity.
- Invent financial values or fill missing MOPS fields.
- Predict stock price or produce investment advice.
- Treat unofficial news as stronger evidence than official filings.
- Hide which source supported a conclusion.

## Why this is still intelligent

The LLM is not reduced to a mechanical extractor. It can synthesize multiple official evidence layers, compare management's conference narrative with the quantitative rule context, and produce user-facing explanations. The explainability is preserved because every narrative output must be traceable to rule results, official disclosure claims, and source URLs.

## Calibration roadmap

The current thresholds are MVP parameters. They are now labeled with `credibility_level` and `calibration_status` so the frontend and LLM can distinguish:

- Official definitions.
- Peer-reviewed or theory-supported logic.
- Company-history thresholds.
- Thresholds still pending peer baseline calibration.

Future calibration should compute same-subindustry peer medians and median absolute deviations (MAD) for foundry, IC design, and packaging/testing instead of using fixed thresholds alone.
