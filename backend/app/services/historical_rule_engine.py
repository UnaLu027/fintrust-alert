from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any

from app.financial_analysis_models import RuleSeverity
from app.historical_analysis_models import (
    HistoricalPeriodRecord,
    HistoricalRuleResult,
    HistoricalTrendMetric,
)


SUBINDUSTRY_RULE_FILES = {
    "晶圓代工": "foundry_historical_rules.json",
    "IC 設計": "ic_design_historical_rules.json",
    "封裝測試": "packaging_testing_historical_rules.json",
}


class HistoricalFinancialRuleEngine:
    def __init__(
        self,
        rules_path: str | Path | None = None,
        *,
        subindustry: str | None = None,
    ) -> None:
        rules_dir = Path(__file__).resolve().parents[1] / "rules"
        default_path = rules_dir / "semiconductor_historical_rules.json"
        selected_path = Path(rules_path) if rules_path else default_path
        common = json.loads(selected_path.read_text(encoding="utf-8"))
        combined_rules = list(common["rules"])
        versions = [str(common["version"])]
        threshold_bases = [str(common["threshold_basis"])]

        if rules_path is None and subindustry in SUBINDUSTRY_RULE_FILES:
            subindustry_config = json.loads(
                (rules_dir / SUBINDUSTRY_RULE_FILES[subindustry]).read_text(encoding="utf-8")
            )
            combined_rules.extend(subindustry_config["rules"])
            versions.append(str(subindustry_config["version"]))
            threshold_bases.append(str(subindustry_config["threshold_basis"]))

        self.rules_path = selected_path
        self.config = {
            **common,
            "version": "+".join(versions),
            "threshold_basis": "；".join(threshold_bases),
            "rules": combined_rules,
        }
        self.subindustry = subindustry

    @property
    def version(self) -> str:
        return str(self.config["version"])

    @property
    def threshold_basis(self) -> str:
        return str(self.config["threshold_basis"])

    @staticmethod
    def _values(metric: HistoricalTrendMetric | None) -> list[tuple[str, float]]:
        if metric is None:
            return []
        return sorted(metric.period_values.items())

    @staticmethod
    def _result(
        rule: dict[str, Any],
        severity: RuleSeverity,
        explanation: str,
        threshold_description: str,
        periods: list[str],
        *,
        actual_values: dict[str, float | None] | None = None,
    ) -> HistoricalRuleResult:
        return HistoricalRuleResult(
            rule_id=rule["rule_id"],
            name=rule["name"],
            category=rule["category"],
            severity=severity,
            triggered=severity
            in {
                RuleSeverity.ATTENTION,
                RuleSeverity.HIGH_ATTENTION,
                RuleSeverity.DATA_ISSUE,
            },
            explanation=explanation,
            threshold_description=threshold_description,
            evidence_periods=periods,
            evidence_metrics=list(rule.get("metrics", [])),
            rule_scope=str(rule.get("rule_scope", "semiconductor_common")),
            logic_expression=rule.get("logic_expression"),
            actual_values=actual_values or {},
        )

    def _insufficient(self, rule: dict[str, Any], message: str) -> HistoricalRuleResult:
        return self._result(
            rule,
            RuleSeverity.INSUFFICIENT_DATA,
            message,
            "缺少規則所需的連續年度或財報欄位。",
            [],
        )

    def evaluate(
        self,
        periods: list[HistoricalPeriodRecord],
        metrics: list[HistoricalTrendMetric],
    ) -> list[HistoricalRuleResult]:
        available_periods = [period for period in periods if period.status == "available"]
        metric_map = {metric.code: metric for metric in metrics}
        results: list[HistoricalRuleResult] = []

        for rule in self.config["rules"]:
            operator = rule["operator"]
            thresholds = rule.get("thresholds", {})
            required = [metric_map.get(code) for code in rule.get("metrics", [])]

            if operator == "minimum_available_years":
                minimum = int(thresholds["minimum"])
                count = len(available_periods)
                severity = RuleSeverity.DATA_ISSUE if count < minimum else RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        (
                            f"目前取得 {count} 個完整年度；至少需要 {minimum} 年才能形成長期趨勢。"
                            if count < minimum
                            else f"目前取得 {count} 個完整年度，已達最低歷史資料涵蓋要求。"
                        ),
                        f"可用完整年度至少 {minimum} 年",
                        [period.period for period in available_periods],
                        actual_values={"available_years": float(count)},
                    )
                )
                continue

            if any(metric is None or not metric.period_values for metric in required):
                results.append(self._insufficient(rule, "缺少此規則需要的歷史指標資料，暫不判斷。"))
                continue

            if operator == "two_consecutive_below":
                metric = required[0]
                values = self._values(metric)
                if len(values) < 2:
                    results.append(self._insufficient(rule, "至少需要兩個連續可比較年度。"))
                    continue
                latest_two = values[-2:]
                high = float(thresholds["high"])
                attention = float(thresholds["attention"])
                latest_values = [value for _, value in latest_two]
                if all(value <= high for value in latest_values):
                    severity = RuleSeverity.HIGH_ATTENTION
                elif all(value < attention for value in latest_values):
                    severity = RuleSeverity.ATTENTION
                else:
                    severity = RuleSeverity.NORMAL
                text = "、".join(f"{period} {value:.2f}{metric.unit}" for period, value in latest_two)
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"最近兩期為 {text}。{rule['rationale']}",
                        f"連續兩期低於 {attention}{metric.unit}；高關注門檻 {high}{metric.unit}",
                        [period for period, _ in latest_two],
                        actual_values={period: value for period, value in latest_two},
                    )
                )
                continue

            if operator == "latest_change_below":
                metric = required[0]
                change = metric.change_percentage_points
                if change is None:
                    results.append(self._insufficient(rule, "缺少兩個年度的比率資料，無法計算百分點變化。"))
                    continue
                if change <= float(thresholds["high"]):
                    severity = RuleSeverity.HIGH_ATTENTION
                elif change <= float(thresholds["attention"]):
                    severity = RuleSeverity.ATTENTION
                else:
                    severity = RuleSeverity.NORMAL
                periods_used = [period for period, _ in self._values(metric)[-2:]]
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{metric.label}最新年度較前一年度變化 {change:.2f} 個百分點。{rule['rationale']}",
                        f"需注意 ≤ {thresholds['attention']}；高關注 ≤ {thresholds['high']} 個百分點",
                        periods_used,
                        actual_values={"change_percentage_points": change},
                    )
                )
                continue

            if operator == "latest_gap_above":
                left, right = required
                left_values = dict(self._values(left))
                right_values = dict(self._values(right))
                common = sorted(set(left_values) & set(right_values))
                if not common:
                    results.append(self._insufficient(rule, "兩項成長率沒有共同年度。"))
                    continue
                latest_period = common[-1]
                left_value = left_values[latest_period]
                right_value = right_values[latest_period]
                gap = left_value - right_value
                if gap >= float(thresholds["high"]):
                    severity = RuleSeverity.HIGH_ATTENTION
                elif gap >= float(thresholds["attention"]):
                    severity = RuleSeverity.ATTENTION
                else:
                    severity = RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{latest_period} 存貨年增 {left_value:.2f}%，營收年增 {right_value:.2f}%，差距 {gap:.2f} 個百分點。{rule['rationale']}",
                        f"差距 ≥ {thresholds['attention']} 個百分點；高關注 ≥ {thresholds['high']} 個百分點",
                        [latest_period],
                        actual_values={left.code: left_value, right.code: right_value, "gap": gap},
                    )
                )
                continue

            if operator == "positive_profit_negative_ocf":
                net_margin, ocf = required
                net_values = dict(self._values(net_margin))
                ocf_values = dict(self._values(ocf))
                common = sorted(set(net_values) & set(ocf_values))
                if not common:
                    results.append(self._insufficient(rule, "淨利率與營業現金流沒有共同年度。"))
                    continue
                latest_period = common[-1]
                profit_value = net_values[latest_period]
                ocf_value = ocf_values[latest_period]
                triggered = profit_value > 0 and ocf_value < 0
                severity = RuleSeverity.HIGH_ATTENTION if triggered else RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{latest_period} 淨利率 {profit_value:.2f}%，營業活動現金流 {ocf_value:,.0f} 新台幣仟元。{rule['rationale']}",
                        "淨利率 > 0 且營業活動現金流 < 0",
                        [latest_period],
                        actual_values={net_margin.code: profit_value, ocf.code: ocf_value},
                    )
                )
                continue

            if operator == "latest_or_two_negative":
                metric = required[0]
                values = self._values(metric)
                if not values:
                    results.append(self._insufficient(rule, "缺少自由現金流資料。"))
                    continue
                latest = values[-1]
                latest_negative = latest[1] < 0
                two_negative = len(values) >= 2 and all(value < 0 for _, value in values[-2:])
                severity = (
                    RuleSeverity.HIGH_ATTENTION
                    if two_negative
                    else RuleSeverity.ATTENTION
                    if latest_negative
                    else RuleSeverity.NORMAL
                )
                periods_used = [period for period, _ in values[-2:]]
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"最近自由現金流為 {latest[1]:,.0f} 新台幣仟元。{rule['rationale']}",
                        "最新年度為負列需注意；連續兩年為負列高關注",
                        periods_used,
                        actual_values={period: value for period, value in values[-2:]},
                    )
                )
                continue

            if operator == "latest_above_median_with_negative":
                capex, fcf = required
                capex_values = self._values(capex)
                fcf_values = dict(self._values(fcf))
                common = sorted(set(dict(capex_values)) & set(fcf_values))
                if len(capex_values) < 3 or not common:
                    results.append(self._insufficient(rule, "至少需要三年資本支出強度及自由現金流。"))
                    continue
                latest_period = common[-1]
                latest_capex = dict(capex_values)[latest_period]
                latest_fcf = fcf_values[latest_period]
                historical = [value for period, value in capex_values if period != latest_period]
                baseline = median(historical) if historical else latest_capex
                gap = latest_capex - baseline
                if latest_fcf < 0 and gap >= float(thresholds["high_gap"]):
                    severity = RuleSeverity.HIGH_ATTENTION
                elif latest_fcf < 0 and gap >= float(thresholds["attention_gap"]):
                    severity = RuleSeverity.ATTENTION
                else:
                    severity = RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{latest_period} 資本支出占營收比 {latest_capex:.2f}%，較先前年度中位數高 {gap:.2f} 個百分點；自由現金流 {latest_fcf:,.0f} 新台幣仟元。{rule['rationale']}",
                        f"自由現金流為負且高於歷史中位數 {thresholds['attention_gap']} 個百分點；高關注 {thresholds['high_gap']} 個百分點",
                        [latest_period],
                        actual_values={capex.code: latest_capex, fcf.code: latest_fcf, "historical_median": baseline, "gap": gap},
                    )
                )
                continue

            if operator == "latest_level_and_change_above":
                metric = required[0]
                values = self._values(metric)
                if len(values) < 2:
                    results.append(self._insufficient(rule, "至少需要兩年負債比。"))
                    continue
                latest_period, latest = values[-1]
                previous = values[-2][1]
                change = latest - previous
                if latest >= float(thresholds["level_high"]) and change >= float(thresholds["change_attention"]):
                    severity = RuleSeverity.HIGH_ATTENTION
                elif latest >= float(thresholds["level_attention"]) and change >= float(thresholds["change_attention"]):
                    severity = RuleSeverity.ATTENTION
                else:
                    severity = RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{latest_period} 負債比 {latest:.2f}%，較前一年度增加 {change:.2f} 個百分點。{rule['rationale']}",
                        f"負債比 ≥ {thresholds['level_attention']}% 且增加 ≥ {thresholds['change_attention']} 個百分點",
                        [values[-2][0], latest_period],
                        actual_values={"latest": latest, "previous": previous, "change_percentage_points": change},
                    )
                )
                continue

            if operator == "informational_trend":
                metric = required[0]
                change = metric.change_percentage_points
                if change is None:
                    results.append(self._insufficient(rule, "缺少兩年研發強度資料。"))
                    continue
                material = abs(change) >= float(thresholds["material_change"])
                severity = RuleSeverity.POSITIVE if material and change > 0 else RuleSeverity.NORMAL
                direction = "增加" if change > 0 else "下降" if change < 0 else "持平"
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"研發費用占營收比較前一年度{direction} {abs(change):.2f} 個百分點。{rule['rationale']}",
                        f"變化絕對值 ≥ {thresholds['material_change']} 個百分點列為重大趨勢觀察",
                        [period for period, _ in self._values(metric)[-2:]],
                        actual_values={"change_percentage_points": change},
                    )
                )
                continue

            if operator == "foundry_capex_margin_pressure":
                capex, fcf, gross_margin = required
                capex_values = self._values(capex)
                fcf_values = dict(self._values(fcf))
                gross_values = self._values(gross_margin)
                common = sorted(set(dict(capex_values)) & set(fcf_values) & set(dict(gross_values)))
                if len(capex_values) < 3 or len(gross_values) < 2 or not common:
                    results.append(self._insufficient(rule, "至少需要三年資本支出與兩年毛利率資料。"))
                    continue
                latest_period = common[-1]
                latest_capex = dict(capex_values)[latest_period]
                latest_fcf = fcf_values[latest_period]
                baseline_values = [value for period, value in capex_values if period != latest_period]
                baseline = median(baseline_values)
                capex_gap = latest_capex - baseline
                margin_change = gross_margin.change_percentage_points
                if margin_change is None:
                    results.append(self._insufficient(rule, "缺少毛利率百分點變化。"))
                    continue
                high = (
                    capex_gap >= float(thresholds["high_capex_gap"])
                    and latest_fcf < 0
                    and margin_change <= float(thresholds["high_margin_drop"])
                )
                attention = (
                    capex_gap >= float(thresholds["attention_capex_gap"])
                    and latest_fcf < 0
                    and margin_change <= float(thresholds["attention_margin_drop"])
                )
                severity = RuleSeverity.HIGH_ATTENTION if high else RuleSeverity.ATTENTION if attention else RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{latest_period} 資本支出強度較歷史中位數高 {capex_gap:.2f} 個百分點，自由現金流 {latest_fcf:,.0f} 新台幣仟元，毛利率變化 {margin_change:.2f} 個百分點。{rule['rationale']}",
                        "資本支出高於歷史基準＋自由現金流為負＋毛利率下滑",
                        [period for period, _ in gross_values[-2:]],
                        actual_values={"capex_intensity": latest_capex, "capex_historical_median": baseline, "capex_gap": capex_gap, "free_cash_flow": latest_fcf, "gross_margin_change_pp": margin_change},
                    )
                )
                continue

            if operator == "ic_design_rd_conversion_pressure":
                rd, revenue_growth, inventory_growth, cash_conversion = required
                rd_change = rd.change_percentage_points
                revenue_values = self._values(revenue_growth)
                inventory_values = dict(self._values(inventory_growth))
                cash_values = dict(self._values(cash_conversion))
                common = sorted(set(dict(revenue_values)) & set(inventory_values) & set(cash_values))
                if rd_change is None or not common:
                    results.append(self._insufficient(rule, "缺少研發強度變化或共同年度營收、存貨與現金轉換資料。"))
                    continue
                latest_period = common[-1]
                revenue_value = dict(revenue_values)[latest_period]
                inventory_value = inventory_values[latest_period]
                cash_value = cash_values[latest_period]
                inventory_gap = inventory_value - revenue_value
                high = (
                    rd_change >= float(thresholds["rd_change_min"])
                    and revenue_value < 0
                    and inventory_gap >= float(thresholds["high_inventory_gap"])
                    and cash_value < float(thresholds["high_cash_conversion_max"])
                )
                attention = (
                    rd_change >= float(thresholds["rd_change_min"])
                    and revenue_value < 0
                    and inventory_gap >= float(thresholds["attention_inventory_gap"])
                    and cash_value < float(thresholds["attention_cash_conversion_max"])
                )
                severity = RuleSeverity.HIGH_ATTENTION if high else RuleSeverity.ATTENTION if attention else RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{latest_period} 研發強度變化 {rd_change:.2f} 個百分點、營收年增 {revenue_value:.2f}%、存貨年增 {inventory_value:.2f}%（差距 {inventory_gap:.2f} 個百分點）、現金轉換比 {cash_value:.2f} 倍。{rule['rationale']}",
                        "研發強度未下降＋營收衰退＋存貨增速高於營收＋現金轉換偏弱",
                        [latest_period],
                        actual_values={"rd_intensity_change_pp": rd_change, "revenue_growth_yoy": revenue_value, "inventory_growth_yoy": inventory_value, "inventory_revenue_gap": inventory_gap, "cash_conversion_ratio": cash_value},
                    )
                )
                continue

            if operator == "packaging_working_capital_pressure":
                inventory_growth, revenue_growth, ocf, debt_ratio = required
                inventory_values = dict(self._values(inventory_growth))
                revenue_values = dict(self._values(revenue_growth))
                common = sorted(set(inventory_values) & set(revenue_values))
                if not common or ocf.change_percent is None or debt_ratio.change_percentage_points is None:
                    results.append(self._insufficient(rule, "缺少共同年度存貨、營收、現金流或負債比變化資料。"))
                    continue
                latest_period = common[-1]
                inventory_value = inventory_values[latest_period]
                revenue_value = revenue_values[latest_period]
                inventory_gap = inventory_value - revenue_value
                ocf_change = ocf.change_percent
                debt_change = debt_ratio.change_percentage_points
                high = (
                    inventory_gap >= float(thresholds["high_inventory_gap"])
                    and ocf_change < 0
                    and debt_change >= float(thresholds["high_debt_change"])
                )
                attention = (
                    inventory_gap >= float(thresholds["attention_inventory_gap"])
                    and ocf_change < 0
                    and debt_change >= float(thresholds["attention_debt_change"])
                )
                severity = RuleSeverity.HIGH_ATTENTION if high else RuleSeverity.ATTENTION if attention else RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{latest_period} 存貨與營收成長差距 {inventory_gap:.2f} 個百分點、營業現金流變化 {ocf_change:.2f}%、負債比變化 {debt_change:.2f} 個百分點。{rule['rationale']}",
                        "存貨增速高於營收＋營業現金流下降＋負債比上升",
                        [latest_period],
                        actual_values={"inventory_growth_yoy": inventory_value, "revenue_growth_yoy": revenue_value, "inventory_revenue_gap": inventory_gap, "operating_cash_flow_change_percent": ocf_change, "debt_ratio_change_pp": debt_change},
                    )
                )
                continue

            raise ValueError(f"Unsupported historical rule operator: {operator}")

        return results
