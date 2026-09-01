from app.financial_analysis_models import NormalizedFinancialStatement
from app.services.financial_metrics import calculate_financial_metrics


def metric_map(statement: NormalizedFinancialStatement):
    return {metric.code: metric for metric in calculate_financial_metrics(statement)}


def test_calculates_profitability_structure_and_growth_metrics():
    statement = NormalizedFinancialStatement(
        ticker="2330",
        company_name="台積電",
        subindustry="晶圓代工",
        report_period="2025Q2",
        revenue=1000,
        gross_profit=580,
        operating_income=450,
        net_income=390,
        total_assets=3000,
        total_liabilities=1100,
        equity=1900,
        current_assets=1200,
        current_liabilities=500,
        inventory=200,
        eps=15.2,
        monthly_revenue=250,
        previous_month_revenue=230,
        prior_year_month_revenue=200,
        monthly_revenue_yoy_reported=25,
    )

    metrics = metric_map(statement)
    assert metrics["gross_margin"].value == 58
    assert metrics["operating_margin"].value == 45
    assert metrics["net_margin"].value == 39
    assert round(metrics["debt_ratio"].value, 2) == 36.67
    assert metrics["current_ratio"].value == 240
    assert metrics["accounting_equation_gap_percent"].value == 0
    assert metrics["monthly_revenue_yoy"].value == 25
    assert metrics["monthly_revenue_yoy_reported_gap"].value == 0
    assert round(metrics["monthly_revenue_mom"].value, 2) == 8.7


def test_skips_ratio_when_denominator_is_zero():
    statement = NormalizedFinancialStatement(
        ticker="2454",
        company_name="聯發科",
        subindustry="IC 設計",
        revenue=0,
        gross_profit=100,
    )
    metrics = metric_map(statement)
    assert "gross_margin" not in metrics
