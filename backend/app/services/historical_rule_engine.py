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


class HistoricalFinancialRuleEngine:
    def __init__(self, rules_path: str | Path | None = None) -> None:
        default_path = (
            Path(__file__).resolve().parents[1]
            / "rules"
            / "semiconductor_historical_rules.json"
        )
        self.rules_path = Path(rules_path) if rules_path else default_path
        self.config = json.loads(self.rules_path.read_text(encoding="utf-8"))

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
                severity = (
                    RuleSeverity.DATA_ISSUE if count < minimum else RuleSeverity.NORMAL
                )
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
                    )
                )
                continue

            if operator == "latest_gap_above":
                left, right = required
                left_values = self._values(left)
                right_values = self._values(right)
                common = sorted(set(dict(left_values)) & set(dict(right_values)))
                if not common:
                    results.append(self._insufficient(rule, "兩項成長率沒有共同年度。"))
                    continue
                latest_period = common[-1]
                left_value = dict(left_values)[latest_period]
                right_value = dict(right_values)[latest_period]
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
                    )
                )
                continue

            if operator == "positive_profit_negative_ocf":
                net_margin, ocf = required
                net_values = self._values(net_margin)
                ocf_values = self._values(ocf)
                common = sorted(set(dict(net_values)) & set(dict(ocf_values)))
                if not common:
                    results.append(self._insufficient(rule, "淨利率與營業現金流沒有共同年度。"))
                    continue
                latest_period = common[-1]
                profit_value = dict(net_values)[latest_period]
                ocf_value = dict(ocf_values)[latest_period]
                triggered = profit_value > 0 and ocf_value < 0
                severity = RuleSeverity.HIGH_ATTENTION if triggered else RuleSeverity.NORMAL
                results.append(
                    self._result(
                        rule,
                        severity,
                        f"{latest_period} 淨利率 {profit_value:.2f}%，營業活動現金流 {ocf_value:,.0f} 新台幣仟元。{rule['rationale']}",
                        "淨利率 > 0 且營業活動現金流 < 0",
                        [latest_period],
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
                    )
                )
                continue

            if operator == "latest_above_median_with_negative":
                capex, fcf = required
                capex_values = self._values(capex)
                fcf_values = self._values(fcf)
                common = sorted(set(dict(capex_values)) & set(dict(fcf_values)))
                if len(capex_values) < 3 or not common:
                    results.append(self._insufficient(rule, "至少需要三年資本支出強度及自由現金流。"))
                    continue
                latest_period = common[-1]
                latest_capex = dict(capex_values)[latest_period]
                latest_fcf = dict(fcf_values)[latest_period]
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
                    )
                )
                continue

            raise ValueError(f"Unsupported historical rule operator: {operator}")

        return results
