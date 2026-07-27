from datetime import datetime, timezone

from app.financial_analysis_models import (
    CalculatedMetric,
    FinancialStatementAnalysisReport,
    NormalizedFinancialStatement,
    RuleResult,
    RuleSeverity,
    SourceCoverage,
)
from app.historical_analysis_models import (
    HistoricalFinancialAnalysisReport,
    HistoricalPeriodRecord,
    HistoricalRuleResult,
    HistoricalTrendMetric,
)
from app.services.analysis_repository import SqliteAnalysisRepository
from app.services.frontend_presenter import build_frontend_snapshot


def test_sqlite_repository_persists_pipeline_and_snapshot(tmp_path):
    now = datetime.now(timezone.utc)
    latest = FinancialStatementAnalysisReport(
        ticker="2330",
        company_name="台積電",
        subindustry="晶圓代工",
        report_period="2024Q4",
        monthly_revenue_period="2024-12",
        analyzed_at=now,
        rule_version="latest-1",
        threshold_basis="test",
        overall_severity=RuleSeverity.NORMAL,
        summary="latest summary",
        statement=NormalizedFinancialStatement(
            ticker="2330",
            company_name="台積電",
            subindustry="晶圓代工",
            report_period="2024Q4",
            revenue=1000,
            total_assets=2000,
            total_liabilities=500,
            source_coverage=[
                SourceCoverage(
                    source_name="TWSE",
                    source_url="https://openapi.twse.com.tw/",
                    status="available",
                    report_period="2024Q4",
                )
            ],
        ),
        metrics=[
            CalculatedMetric(
                code="debt_ratio",
                label="負債比",
                category="財務結構",
                value=25,
                unit="%",
                formula="負債÷資產×100",
                inputs={"total_liabilities": 500, "total_assets": 2000},
                source_fields=["total_liabilities", "total_assets"],
            )
        ],
        rule_results=[
            RuleResult(
                rule_id="LATEST_001",
                name="test latest",
                category="test",
                severity=RuleSeverity.NORMAL,
                triggered=False,
                metric_code="debt_ratio",
                actual_value=25,
                unit="%",
                threshold_description="test",
                explanation="test",
                evidence_metrics=["debt_ratio"],
            )
        ],
    )

    periods = [
        HistoricalPeriodRecord(
            ticker="2330",
            company_name="台積電",
            subindustry="晶圓代工",
            fiscal_year=year,
            roc_year=year - 1911,
            period=f"{year}FY",
            source_url=f"https://mops.example/{year}",
            status="available",
            revenue=900 + (year - 2022) * 50,
            gross_profit=450,
            operating_cash_flow=300,
            capital_expenditure=-200,
            total_assets=2000,
            total_liabilities=500,
            concept_matches={"revenue": "Revenue"},
        )
        for year in (2022, 2023, 2024)
    ]
    historical = HistoricalFinancialAnalysisReport(
        ticker="2330",
        company_name="台積電",
        subindustry="晶圓代工",
        requested_years=3,
        available_years=3,
        start_year=2022,
        end_year=2024,
        analyzed_at=now,
        rule_version="history-1",
        threshold_basis="test",
        overall_severity=RuleSeverity.ATTENTION,
        summary="historical summary",
        periods=periods,
        trend_metrics=[
            HistoricalTrendMetric(
                code="capex_intensity",
                label="資本支出占營收比",
                category="半導體資本投入",
                unit="%",
                period_values={"2022FY": 20, "2023FY": 21, "2024FY": 22},
                latest_value=22,
                previous_value=21,
                change_percentage_points=1,
                formula="資本支出÷營收×100",
                source_fields=["capital_expenditure", "revenue"],
            )
        ],
        rule_results=[
            HistoricalRuleResult(
                rule_id="FOUNDRY_001",
                name="foundry test",
                category="晶圓代工",
                severity=RuleSeverity.ATTENTION,
                triggered=True,
                explanation="test",
                threshold_description="test",
                evidence_periods=["2024FY"],
                evidence_metrics=["capex_intensity"],
                rule_scope="foundry",
                logic_expression="capex_intensity > baseline",
                actual_values={"capex_intensity": 22},
            )
        ],
    )

    snapshot = build_frontend_snapshot(
        run_id="run-test",
        latest_report=latest,
        historical_report=historical,
    )
    repository = SqliteAnalysisRepository(str(tmp_path / "pipeline.sqlite3"))
    counts = repository.save_pipeline_result(
        run_id="run-test",
        trigger="demo",
        started_at=now,
        completed_at=now,
        latest_report=latest,
        historical_report=historical,
        snapshot=snapshot,
    )

    assert counts.filings == 3
    assert counts.snapshots == 1
    assert repository.get_latest_snapshot("2330") == snapshot
    assert repository.list_metrics("2330")
    assert repository.list_runs("2330")[0].run_id == "run-test"
