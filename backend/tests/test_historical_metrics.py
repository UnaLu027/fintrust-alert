from app.historical_analysis_models import HistoricalPeriodRecord
from app.services.historical_metrics import calculate_historical_metrics


def period(year: int, **values) -> HistoricalPeriodRecord:
    return HistoricalPeriodRecord(
        ticker="2330",
        company_name="台積電",
        subindustry="晶圓代工",
        fiscal_year=year,
        roc_year=year - 1911,
        period=f"{year}FY",
        source_url="https://mopsov.twse.com.tw/",
        status="available",
        **values,
    )


def test_calculate_historical_growth_margin_cash_capex_and_turnover_metrics():
    periods = [
        period(
            2022,
            revenue=1000,
            cost_of_goods_sold=500,
            gross_profit=500,
            operating_income=300,
            net_income=200,
            accounts_receivable=80,
            inventory=100,
            operating_cash_flow=250,
            capital_expenditure=-150,
            research_and_development_expense=80,
            total_assets=2000,
            total_liabilities=600,
            current_assets=800,
            current_liabilities=400,
        ),
        period(
            2023,
            revenue=1100,
            cost_of_goods_sold=572,
            gross_profit=528,
            operating_income=286,
            net_income=220,
            accounts_receivable=88,
            inventory=130,
            operating_cash_flow=210,
            capital_expenditure=-180,
            research_and_development_expense=99,
            total_assets=2200,
            total_liabilities=770,
            current_assets=880,
            current_liabilities=440,
        ),
        period(
            2024,
            revenue=1210,
            cost_of_goods_sold=665.5,
            gross_profit=544.5,
            operating_income=290.4,
            net_income=242,
            accounts_receivable=96.8,
            inventory=182,
            operating_cash_flow=300,
            capital_expenditure=-220,
            research_and_development_expense=121,
            total_assets=2400,
            total_liabilities=960,
            current_assets=900,
            current_liabilities=500,
        ),
    ]

    metrics = {metric.code: metric for metric in calculate_historical_metrics(periods)}

    assert metrics["revenue_growth_yoy"].period_values["2023FY"] == 10
    assert metrics["revenue_growth_yoy"].period_values["2024FY"] == 10
    assert metrics["gross_margin"].period_values["2022FY"] == 50
    assert metrics["gross_margin"].period_values["2024FY"] == 45
    assert metrics["gross_margin"].change_percentage_points == -3
    assert metrics["cash_conversion_ratio"].period_values["2023FY"] == 0.9545
    assert metrics["free_cash_flow"].period_values["2024FY"] == 80
    assert round(metrics["capex_intensity"].period_values["2024FY"], 2) == 18.18
    assert metrics["rd_intensity"].period_values["2024FY"] == 10
    assert metrics["debt_ratio"].period_values["2024FY"] == 40
    assert round(metrics["inventory_turnover_days"].period_values["2023FY"], 2) == 73.38
    assert round(metrics["receivable_turnover_days"].period_values["2023FY"], 2) == 27.87
