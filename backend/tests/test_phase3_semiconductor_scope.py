from app.services.company_registry import get_company, list_companies
from app.services.historical_rule_engine import HistoricalFinancialRuleEngine
from scripts.smoke_semiconductor_companies import (
    PHASE3_COMPANY_TARGETS,
    REQUIRED_METRICS_BY_SUBINDUSTRY,
    build_company_summary,
    phase3_target_profiles,
)
from app.financial_analysis_models import RuleSeverity
from app.historical_analysis_models import (
    HistoricalFinancialAnalysisReport,
    HistoricalRuleResult,
    HistoricalTrendMetric,
)
from datetime import datetime, timezone


def test_phase3_company_targets_cover_teacher_requested_subindustries() -> None:
    assert PHASE3_COMPANY_TARGETS == ("2330", "2303", "2454", "3711")
    profiles = phase3_target_profiles()
    assert profiles == [
        {"ticker": "2330", "company_name": "台積電", "subindustry": "晶圓代工"},
        {"ticker": "2303", "company_name": "聯電", "subindustry": "晶圓代工"},
        {"ticker": "2454", "company_name": "聯發科", "subindustry": "IC 設計"},
        {"ticker": "3711", "company_name": "日月光投控", "subindustry": "封裝測試"},
    ]
    registered_tickers = {company.ticker for company in list_companies()}
    assert set(PHASE3_COMPANY_TARGETS).issubset(registered_tickers)


def test_phase3_required_metrics_are_subindustry_specific() -> None:
    assert "capex_intensity" in REQUIRED_METRICS_BY_SUBINDUSTRY["晶圓代工"]
    assert "rd_intensity" in REQUIRED_METRICS_BY_SUBINDUSTRY["IC 設計"]
    assert "inventory_growth_yoy" in REQUIRED_METRICS_BY_SUBINDUSTRY["封裝測試"]
    assert "debt_ratio" in REQUIRED_METRICS_BY_SUBINDUSTRY["封裝測試"]


def test_historical_rule_engine_dispatches_subindustry_rule_files() -> None:
    expected_scope_by_subindustry = {
        "晶圓代工": "foundry",
        "IC 設計": "ic_design",
        "封裝測試": "packaging_testing",
    }
    for subindustry, expected_scope in expected_scope_by_subindustry.items():
        engine = HistoricalFinancialRuleEngine(subindustry=subindustry)
        scopes = {rule.get("rule_scope") for rule in engine.config["rules"]}
        assert "semiconductor_common" in scopes
        assert expected_scope in scopes
        assert subindustry in engine.threshold_basis


def test_get_company_keeps_phase3_company_aliases() -> None:
    assert get_company("2330").aliases[-1] == "2330"
    assert "UMC" in get_company("2303").aliases
    assert "MediaTek" in get_company("2454").aliases
    assert "ASEH" in get_company("3711").aliases


def test_phase3_summary_reports_missing_metrics_and_rule_scopes() -> None:
    report = HistoricalFinancialAnalysisReport(
        ticker="3711",
        company_name="日月光投控",
        subindustry="封裝測試",
        requested_years=3,
        available_years=3,
        start_year=2022,
        end_year=2024,
        analyzed_at=datetime.now(timezone.utc),
        rule_version="semiconductor-history-mvp-0.1.0+packaging-testing-history-0.1.0",
        threshold_basis="封裝測試營運資金、產能投入與負債結構＋公司自身歷史趨勢；門檻為可調整 MVP 參數",
        overall_severity=RuleSeverity.NORMAL,
        summary="日月光投控已取得 3 個可用年度。",
        periods=[],
        trend_metrics=[
            HistoricalTrendMetric(
                code="revenue_growth_yoy",
                label="營收年增率",
                category="成長性",
                unit="%",
                period_values={"2024FY": 5.0},
                latest_value=5.0,
                formula="營收年增率",
            ),
            HistoricalTrendMetric(
                code="inventory_growth_yoy",
                label="存貨年增率",
                category="營運效率",
                unit="%",
                period_values={"2024FY": 3.0},
                latest_value=3.0,
                formula="存貨年增率",
            ),
        ],
        rule_results=[
            HistoricalRuleResult(
                rule_id="PACKAGING_WORKING_CAPITAL_001",
                name="存貨、現金流與負債同步壓力",
                category="封裝測試營運資金",
                severity=RuleSeverity.NORMAL,
                triggered=False,
                explanation="測試用。",
                threshold_description="測試用。",
                rule_scope="packaging_testing",
            )
        ],
        limitations=[],
    )
    summary = build_company_summary(report)
    assert summary["ticker"] == "3711"
    assert summary["rule_scope_counts"] == {"packaging_testing": 1}
    assert summary["metric_coverage"]["inventory_growth_yoy"] is True
    assert "operating_cash_flow" in summary["missing_required_metrics"]
    assert summary["ai_v2"]["enabled"] is False
