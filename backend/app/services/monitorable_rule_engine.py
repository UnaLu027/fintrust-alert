from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.ai_analysis_models import (
    AnalysisDimension,
    AnalysisFeatureValue,
    AnalysisRuleCatalogItem,
    AnalysisRuleCatalogResponse,
    DIMENSION_LABELS,
    MonitoredRuleResult,
    RuleEvaluationStatus,
)
from app.financial_analysis_models import RuleSeverity


class MonitorableFinancialRuleEngine:
    """Config-driven rule engine for screenshot-friendly monitoring and later admin editing."""

    def __init__(self, rules_path: str | Path | None = None, *, subindustry: str = "IC 設計") -> None:
        if rules_path is None:
            if subindustry != "IC 設計":
                raise ValueError("AI analysis engine v1 currently provides a full rule catalog for IC 設計.")
            rules_path = Path(__file__).resolve().parents[1] / "rules" / "ic_design_analysis_rules.json"
        self.rules_path = Path(rules_path)
        self.config = json.loads(self.rules_path.read_text(encoding="utf-8"))

    @property
    def version(self) -> str:
        return str(self.config["version"])

    @property
    def subindustry(self) -> str:
        return str(self.config["subindustry"])

    @staticmethod
    def _collect_features(condition: dict[str, Any]) -> set[str]:
        if "feature" in condition:
            return {str(condition["feature"])}
        found: set[str] = set()
        for key in ("all", "any"):
            for child in condition.get(key, []):
                found.update(MonitorableFinancialRuleEngine._collect_features(child))
        if "not" in condition:
            found.update(MonitorableFinancialRuleEngine._collect_features(condition["not"]))
        return found

    @staticmethod
    def _compare(actual: float, op: str, expected: float) -> bool:
        if op == "gt":
            return actual > expected
        if op == "gte":
            return actual >= expected
        if op == "lt":
            return actual < expected
        if op == "lte":
            return actual <= expected
        if op == "eq":
            return actual == expected
        if op == "ne":
            return actual != expected
        raise ValueError(f"Unsupported monitorable rule operator: {op}")

    @classmethod
    def _evaluate_condition(cls, condition: dict[str, Any], feature_values: dict[str, float]) -> bool:
        if "feature" in condition:
            return cls._compare(
                feature_values[str(condition["feature"])],
                str(condition["op"]),
                float(condition["value"]),
            )
        if "all" in condition:
            return all(cls._evaluate_condition(child, feature_values) for child in condition["all"])
        if "any" in condition:
            return any(cls._evaluate_condition(child, feature_values) for child in condition["any"])
        if "not" in condition:
            return not cls._evaluate_condition(condition["not"], feature_values)
        raise ValueError("Rule condition must contain feature, all, any, or not.")

    def catalog(self) -> AnalysisRuleCatalogResponse:
        items: list[AnalysisRuleCatalogItem] = []
        for rule in self.config["rules"]:
            dimension = AnalysisDimension(rule["dimension"])
            required = sorted(self._collect_features(rule["condition"]))
            items.append(
                AnalysisRuleCatalogItem(
                    rule_id=rule["rule_id"],
                    name=rule["name"],
                    dimension=dimension,
                    dimension_label=DIMENSION_LABELS[dimension],
                    assessment_type=rule["assessment_type"],
                    severity=RuleSeverity(rule["severity"]),
                    logic_expression=rule["logic_expression"],
                    rationale=rule["rationale"],
                    direct_metrics=rule.get("direct_metrics", []),
                    indirect_metrics=rule.get("indirect_metrics", []),
                    required_features=required,
                )
            )
        return AnalysisRuleCatalogResponse(
            version=self.version,
            subindustry=self.subindustry,
            rule_count=len(items),
            dimensions=sorted({item.dimension for item in items}, key=lambda item: item.value),
            rules=items,
        )

    def evaluate(self, features: dict[str, AnalysisFeatureValue]) -> list[MonitoredRuleResult]:
        feature_values = {code: feature.value for code, feature in features.items()}
        results: list[MonitoredRuleResult] = []

        for rule in self.config["rules"]:
            dimension = AnalysisDimension(rule["dimension"])
            required = sorted(self._collect_features(rule["condition"]))
            missing = [code for code in required if code not in feature_values]
            actual_values = {code: feature_values.get(code) for code in required}
            if missing:
                results.append(
                    MonitoredRuleResult(
                        rule_id=rule["rule_id"],
                        name=rule["name"],
                        dimension=dimension,
                        dimension_label=DIMENSION_LABELS[dimension],
                        assessment_type=rule["assessment_type"],
                        severity=RuleSeverity.INSUFFICIENT_DATA,
                        evaluation_status=RuleEvaluationStatus.INSUFFICIENT_DATA,
                        triggered=False,
                        logic_expression=rule["logic_expression"],
                        rationale=rule["rationale"],
                        direct_metrics=rule.get("direct_metrics", []),
                        indirect_metrics=rule.get("indirect_metrics", []),
                        required_features=required,
                        missing_features=missing,
                        actual_values=actual_values,
                    )
                )
                continue

            try:
                triggered = self._evaluate_condition(rule["condition"], feature_values)
                severity = RuleSeverity(rule["severity"]) if triggered else RuleSeverity.NORMAL
                status = RuleEvaluationStatus.EVALUATED
                error = None
            except (KeyError, TypeError, ValueError) as exc:
                triggered = False
                severity = RuleSeverity.DATA_ISSUE
                status = RuleEvaluationStatus.ERROR
                error = str(exc)

            rationale = rule["rationale"] if error is None else f"規則執行錯誤：{error}"
            results.append(
                MonitoredRuleResult(
                    rule_id=rule["rule_id"],
                    name=rule["name"],
                    dimension=dimension,
                    dimension_label=DIMENSION_LABELS[dimension],
                    assessment_type=rule["assessment_type"],
                    severity=severity,
                    evaluation_status=status,
                    triggered=triggered,
                    logic_expression=rule["logic_expression"],
                    rationale=rationale,
                    direct_metrics=rule.get("direct_metrics", []),
                    indirect_metrics=rule.get("indirect_metrics", []),
                    required_features=required,
                    missing_features=[],
                    actual_values=actual_values,
                )
            )

        return results
