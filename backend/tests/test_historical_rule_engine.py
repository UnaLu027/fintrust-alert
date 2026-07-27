from app.financial_analysis_models import RuleSeverity
from app.historical_analysis_models import HistoricalPeriodRecord
from app.services.historical_metrics import calculate_historical_metrics
from app.services.historical_rule_engine import HistoricalFinancialRuleEngine


def period(year: int, **values) -> HistoricalPeriodRecord:
    return HistoricalPeriodRecord(
        ticker="2303",
        company_name="聯電",
        subindustry="晶圓代工",
        fiscal_year=year,
        roc_year=year - 1911,
        period=f"{year}FY",
        source_url="https://mopsov.twse.com.tw/",
        status="available",
        **values,
    )


def results_by_id(periods):
    metrics = calculate_historical_metrics(periods)
    return {
        result.rule_id: result
        for result in HistoricalFinancialRuleEngine().evaluate(periods, metrics)
    }


def test_history_rules_detect_revenue_decline_inventory_gap_and_negative_fcf():
    periods = [
        period(
            2022,
            revenue=1000,
            gross_profit=500,
            operating_income=200,
            net_income=100,
            inventory=100,
            operating_cash_flow=180,
            capital_expenditure=-120,
            total_assets=1800,
            total_liabilities=500,
        ),
        period(
            2023,
            revenue=850,
            gross_profit=382.5,
            operating_income=120,
            net_income=80,
            inventory=130,
            operating_cash_flow=70,
            capital_expenditure=-100,
            total_assets=1900,
            total_liabilities=650,
        ),
        period(
            2024,
            revenue=700,
            gross_profit=280,
            operating_income=70,
            net_income=50,
            inventory=182,
            operating_cash_flow=40,
            capital_expenditure=-110,
            total_assets=2000,
            total_liabilities=900,
        ),
    ]

    results = results_by_id(periods)

    assert results["SEM_HIST_GROWTH_001"].severity == RuleSeverity.HIGH_ATTENTION
    assert results["SEM_HIST_PROFIT_001"].severity == RuleSeverity.HIGH_ATTENTION
    assert results["SEM_HIST_INV_001"].severity == RuleSeverity.HIGH_ATTENTION
    assert results["SEM_HIST_FCF_001"].severity == RuleSeverity.HIGH_ATTENTION


def test_history_rule_reports_data_issue_when_less_than_three_years():
    periods = [
        period(2023, revenue=1000, total_assets=2000, net_income=100),
        period(2024, revenue=1100, total_assets=2100, net_income=120),
    ]

    results = results_by_id(periods)

    assert results["SEM_HIST_DATA_001"].severity == RuleSeverity.DATA_ISSUE
    assert results["SEM_HIST_DATA_001"].triggered is True
