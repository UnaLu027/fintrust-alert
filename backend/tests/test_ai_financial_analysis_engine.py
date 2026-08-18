from datetime import datetime, timezone

import httpx
import pytest

from app.financial_analysis_models import RuleSeverity
from app.historical_analysis_models import HistoricalFinancialAnalysisReport, HistoricalPeriodRecord
from app.services.ai_financial_analysis_service import AIFinancialAnalysisService
from app.services.historical_metrics import calculate_historical_metrics
from app.services.llm_financial_analyst import LLMFinancialAnalyst
from app.services.monitorable_rule_engine import MonitorableFinancialRuleEngine


def period(year: int, **values) -> HistoricalPeriodRecord:
    return HistoricalPeriodRecord(
        ticker="2454",
        company_name="聯發科",
        subindustry="IC 設計",
        fiscal_year=year,
        roc_year=year - 1911,
        period=f"{year}FY",
        source_url="https://mops.twse.com.tw/",
        status="available",
        **values,
    )


def sample_report() -> HistoricalFinancialAnalysisReport:
    periods = [
        period(
            2023,
            revenue=1000,
            gross_profit=500,
            operating_income=180,
            net_income=150,
            eps=10,
            inventory=100,
            operating_cash_flow=180,
            capital_expenditure=-20,
            research_and_development_expense=220,
            total_assets=1800,
            total_liabilities=500,
            current_assets=700,
            current_liabilities=300,
        ),
        period(
            2024,
            revenue=1100,
            gross_profit=528,
            operating_income=187,
            net_income=165,
            eps=11,
            inventory=115,
            operating_cash_flow=200,
            capital_expenditure=-25,
            research_and_development_expense=250,
            total_assets=1950,
            total_liabilities=550,
            current_assets=760,
            current_liabilities=320,
        ),
        period(
            2025,
            revenue=1210,
            gross_profit=556.6,
            operating_income=193.6,
            net_income=181.5,
            eps=12.2,
            inventory=125,
            operating_cash_flow=230,
            capital_expenditure=-28,
            research_and_development_expense=285,
            total_assets=2100,
            total_liabilities=590,
            current_assets=820,
            current_liabilities=330,
        ),
    ]
    return HistoricalFinancialAnalysisReport(
        ticker="2454",
        company_name="聯發科",
        subindustry="IC 設計",
        requested_years=3,
        available_years=3,
        start_year=2023,
        end_year=2025,
        analyzed_at=datetime.now(timezone.utc),
        rule_version="existing",
        threshold_basis="test",
        overall_severity=RuleSeverity.NORMAL,
        summary="test",
        periods=periods,
        trend_metrics=calculate_historical_metrics(periods),
        rule_results=[],
    )


def stress_report() -> HistoricalFinancialAnalysisReport:
    periods = [
        period(
            2023,
            revenue=1200,
            gross_profit=600,
            operating_income=240,
            net_income=200,
            eps=12,
            inventory=100,
            operating_cash_flow=230,
            capital_expenditure=-20,
            research_and_development_expense=240,
            total_assets=1800,
            total_liabilities=500,
            current_assets=700,
            current_liabilities=300,
        ),
        period(
            2024,
            revenue=1150,
            gross_profit=552,
            operating_income=207,
            net_income=180,
            eps=10.5,
            inventory=130,
            operating_cash_flow=170,
            capital_expenditure=-22,
            research_and_development_expense=260,
            total_assets=1900,
            total_liabilities=580,
            current_assets=680,
            current_liabilities=320,
        ),
        period(
            2025,
            revenue=1000,
            gross_profit=430,
            operating_income=140,
            net_income=150,
            eps=8.2,
            inventory=190,
            operating_cash_flow=90,
            capital_expenditure=-25,
            research_and_development_expense=280,
            total_assets=1950,
            total_liabilities=700,
            current_assets=600,
            current_liabilities=360,
        ),
    ]
    return HistoricalFinancialAnalysisReport(
        ticker="2454",
        company_name="聯發科",
        subindustry="IC 設計",
        requested_years=3,
        available_years=3,
        start_year=2023,
        end_year=2025,
        analyzed_at=datetime.now(timezone.utc),
        rule_version="existing",
        threshold_basis="test",
        overall_severity=RuleSeverity.ATTENTION,
        summary="stress",
        periods=periods,
        trend_metrics=calculate_historical_metrics(periods),
        rule_results=[],
    )


def test_rule_catalog_has_all_eight_dimensions_and_monitoring_metadata():
    catalog = MonitorableFinancialRuleEngine().catalog()
    assert catalog.rule_count == 24
    assert len(catalog.dimensions) == 8
    assert all(rule.logic_expression for rule in catalog.rules)
    assert all(rule.required_features for rule in catalog.rules)


@pytest.mark.asyncio
async def test_ai_analysis_builds_features_dimensions_and_monitoring_without_llm():
    report = sample_report()
    service = AIFinancialAnalysisService(
        llm_analyst=LLMFinancialAnalyst(endpoint="", api_key="", model="")
    )
    result = await service.analyze_report(report, use_llm=False)
    assert result.feature_count >= 30
    assert len(result.dimension_assessments) == 8
    assert len(result.rule_monitoring) == 24
    assert result.llm_trace.status == "skipped"
    assert any(
        item.rule_id == "IC_GROWTH_001" and item.triggered
        for item in result.rule_monitoring
    )
    assert any(
        item.dimension.value == "growth" and item.signal.value == "positive"
        for item in result.dimension_assessments
    )


@pytest.mark.asyncio
async def test_monitoring_exposes_missing_features_as_insufficient_data():
    report = sample_report()
    report.trend_metrics = [
        metric
        for metric in report.trend_metrics
        if metric.code not in {"rd_intensity", "rd_expense_growth_yoy"}
    ]
    result = await AIFinancialAnalysisService().analyze_report(report, use_llm=False)
    rd_rules = [
        item for item in result.rule_monitoring if item.dimension.value == "rd_innovation"
    ]
    assert any(item.evaluation_status.value == "insufficient_data" for item in rd_rules)
    assert any(item.missing_features for item in rd_rules)


@pytest.mark.asyncio
async def test_cross_factor_stress_scenario_triggers_high_attention():
    result = await AIFinancialAnalysisService().analyze_report(
        stress_report(),
        use_llm=False,
    )
    by_id = {item.rule_id: item for item in result.rule_monitoring}
    assert by_id["IC_GROWTH_003"].triggered is True
    assert by_id["IC_RD_003"].triggered is True
    assert by_id["IC_OPS_002"].triggered is True
    assert any(
        item.signal.value == "high_attention"
        for item in result.dimension_assessments
    )


@pytest.mark.asyncio
async def test_llm_layer_parses_json_and_keeps_trace():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer demo-key"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"executive_summary":"整體基本面穩定。",'
                                '"dimension_insights":{"growth":"成長具一致性"},'
                                '"watch_items":[],"limitations":["僅依已提供證據"]}'
                            )
                        }
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    llm = LLMFinancialAnalyst(
        endpoint="https://example.test/chat",
        api_key="demo-key",
        model="demo-model",
        client=client,
    )
    service = AIFinancialAnalysisService(llm_analyst=llm)
    result = await service.analyze_report(sample_report(), use_llm=True)
    await client.aclose()
    assert result.llm_trace.status == "completed"
    assert result.llm_trace.model == "demo-model"
    assert result.llm_narrative is not None
    assert result.llm_narrative.executive_summary == "整體基本面穩定。"
