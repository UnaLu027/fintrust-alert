from datetime import datetime, timezone
from types import SimpleNamespace

from app.financial_analysis_models import RuleSeverity
from app.services.frontend_presenter import build_frontend_snapshot


def latest_report(overall: RuleSeverity = RuleSeverity.INSUFFICIENT_DATA):
    return SimpleNamespace(
        analyzed_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
        overall_severity=overall,
        summary="台積電本次規則分析結果：高關注 0 項、需注意 0 項、資料一致性問題 0 項、正向觀察 1 項、資料不足 6 項；整體狀態為 insufficient_data。",
        report_period="2026Q2",
        limitations=[],
        statement=SimpleNamespace(source_coverage=[]),
    )


def historical_report(overall: RuleSeverity = RuleSeverity.NORMAL, insufficient_rules: int = 0):
    rule_results = [
        SimpleNamespace(
            rule_id=f"RULE_{index}",
            name="測試規則",
            category="history",
            severity=RuleSeverity.INSUFFICIENT_DATA,
            triggered=False,
            explanation="缺少資料",
            threshold_description="測試門檻",
            evidence_periods=[],
            evidence_metrics=[],
            rule_scope="semiconductor_common",
            logic_expression=None,
            actual_values={},
        )
        for index in range(insufficient_rules)
    ]
    rule_results.extend(
        [
            SimpleNamespace(
                rule_id="NORMAL_RULE",
                name="正常規則",
                category="history",
                severity=RuleSeverity.NORMAL,
                triggered=False,
                explanation="正常",
                threshold_description="測試門檻",
                evidence_periods=["2024FY"],
                evidence_metrics=["gross_margin"],
                rule_scope="foundry",
                logic_expression="gross_margin >= 0",
                actual_values={"gross_margin": 56.12},
            )
        ]
    )
    return SimpleNamespace(
        ticker="2330",
        company_name="台積電",
        subindustry="晶圓代工",
        available_years=3,
        start_year=2022,
        end_year=2024,
        analyzed_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
        overall_severity=overall,
        rule_version="semiconductor-history-mvp-0.1.0+foundry-history-0.1.0",
        threshold_basis="mvp",
        trend_metrics=[],
        rule_results=rule_results,
        periods=[],
        limitations=[],
    )


def test_latest_twse_insufficient_data_does_not_make_snapshot_look_failed():
    snapshot = build_frontend_snapshot(
        run_id="run-1",
        latest_report=latest_report(),
        historical_report=historical_report(),
    )

    assert snapshot.overall_severity == RuleSeverity.NORMAL
    assert "官方財報資料管線" in snapshot.summary
    assert "資料不足 0 項" in snapshot.summary
    assert "資料不足 6 項" not in snapshot.summary
    assert "insufficient_data" not in snapshot.summary


def test_historical_insufficient_data_is_still_visible():
    snapshot = build_frontend_snapshot(
        run_id="run-2",
        latest_report=latest_report(overall=RuleSeverity.POSITIVE),
        historical_report=historical_report(
            overall=RuleSeverity.INSUFFICIENT_DATA,
            insufficient_rules=1,
        ),
    )

    assert snapshot.overall_severity == RuleSeverity.INSUFFICIENT_DATA
    assert "資料不足 1 項" in snapshot.summary
