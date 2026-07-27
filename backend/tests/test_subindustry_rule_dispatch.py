from app.financial_analysis_models import RuleSeverity
from app.historical_analysis_models import HistoricalPeriodRecord
from app.services.historical_metrics import calculate_historical_metrics
from app.services.historical_rule_engine import HistoricalFinancialRuleEngine


def _period(year: int, **values) -> HistoricalPeriodRecord:
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


def test_foundry_rule_is_loaded_and_exposes_logic():
    periods = [
        _period(
            2022,
            revenue=1000,
            gross_profit=500,
            net_income=100,
            operating_cash_flow=250,
            capital_expenditure=-180,
            total_assets=2000,
            total_liabilities=500,
        ),
        _period(
            2023,
            revenue=1100,
            gross_profit=528,
            net_income=100,
            operating_cash_flow=220,
            capital_expenditure=-220,
            total_assets=2100,
            total_liabilities=550,
        ),
        _period(
            2024,
            revenue=1000,
            gross_profit=400,
            net_income=80,
            operating_cash_flow=180,
            capital_expenditure=-500,
            total_assets=2300,
            total_liabilities=650,
        ),
    ]
    metrics = calculate_historical_metrics(periods)
    results = {
        result.rule_id: result
        for result in HistoricalFinancialRuleEngine(subindustry="晶圓代工").evaluate(
            periods, metrics
        )
    }

    result = results["FOUNDRY_CAPEX_MARGIN_001"]
    assert result.rule_scope == "foundry"
    assert result.logic_expression is not None
    assert result.actual_values["capex_intensity"] == 50.0
    assert result.severity in {RuleSeverity.ATTENTION, RuleSeverity.HIGH_ATTENTION}
