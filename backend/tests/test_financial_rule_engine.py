from app.financial_analysis_models import CalculatedMetric, RuleSeverity
from app.services.financial_rule_engine import FinancialRuleEngine


def metric(code: str, value: float, unit: str = "%") -> CalculatedMetric:
    return CalculatedMetric(
        code=code,
        label=code,
        category="test",
        value=value,
        unit=unit,
        formula="test formula",
    )


def result_map(metrics):
    engine = FinancialRuleEngine()
    return {result.rule_id: result for result in engine.evaluate(metrics)}


def test_flags_high_revenue_decline_and_negative_operating_margin():
    results = result_map(
        [
            metric("monthly_revenue_yoy", -25),
            metric("monthly_revenue_mom", -5),
            metric("operating_margin", -8),
            metric("net_margin", 3),
            metric("current_ratio", 150),
            metric("debt_ratio", 40),
            metric("equity_value", 1000, "新台幣仟元"),
            metric("accounting_equation_gap_percent", 0),
            metric("monthly_revenue_yoy_reported_gap", 0),
        ]
    )
    assert results["SEM_GROWTH_001"].severity == RuleSeverity.HIGH_ATTENTION
    assert results["SEM_PROFIT_001"].severity == RuleSeverity.HIGH_ATTENTION
    assert results["SEM_GROWTH_002"].severity == RuleSeverity.NORMAL


def test_marks_accounting_gap_as_data_issue():
    results = result_map([metric("accounting_equation_gap_percent", 1.2)])
    assert results["SEM_DATA_001"].severity == RuleSeverity.DATA_ISSUE
    assert results["SEM_DATA_001"].triggered is True


def test_missing_metric_returns_insufficient_data_not_false_alarm():
    results = result_map([])
    assert results["SEM_PROFIT_001"].severity == RuleSeverity.INSUFFICIENT_DATA
    assert results["SEM_PROFIT_001"].triggered is False
