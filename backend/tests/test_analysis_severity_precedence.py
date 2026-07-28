from types import SimpleNamespace

from app.financial_analysis_models import RuleSeverity
from app.services.financial_analysis_service import FinancialAnalysisService
from app.services.historical_analysis_service import HistoricalFinancialAnalysisService


def result(severity: RuleSeverity):
    return SimpleNamespace(severity=severity)


def test_latest_insufficient_data_is_not_hidden_by_positive_rule():
    severity = FinancialAnalysisService._overall_severity(
        [result(RuleSeverity.POSITIVE), result(RuleSeverity.INSUFFICIENT_DATA)]
    )
    assert severity == RuleSeverity.INSUFFICIENT_DATA


def test_historical_insufficient_data_is_not_reported_as_normal():
    severity = HistoricalFinancialAnalysisService._overall_severity(
        [result(RuleSeverity.NORMAL), result(RuleSeverity.INSUFFICIENT_DATA)]
    )
    assert severity == RuleSeverity.INSUFFICIENT_DATA


def test_attention_still_has_precedence_over_insufficient_data():
    severity = HistoricalFinancialAnalysisService._overall_severity(
        [result(RuleSeverity.ATTENTION), result(RuleSeverity.INSUFFICIENT_DATA)]
    )
    assert severity == RuleSeverity.ATTENTION
