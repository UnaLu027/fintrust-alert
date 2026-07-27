from app.models import CompanyProfile
from app.services.statement_normalizer import normalize_twse_bundle, parse_number


def profile() -> CompanyProfile:
    return CompanyProfile(
        ticker="2330",
        name="台積電",
        subindustry="晶圓代工",
        aliases=["台積電", "2330"],
    )


def test_parse_number_handles_commas_percent_and_parentheses():
    assert parse_number("1,234,567") == 1234567
    assert parse_number("12.5%") == 12.5
    assert parse_number("(800)") == -800
    assert parse_number("-") is None


def test_normalize_twse_bundle_maps_financial_fields():
    bundle = {
        "income_statement": {
            "公司代號": "2330",
            "年度": "114",
            "季別": "2",
            "營業收入": "1,000,000",
            "營業毛利（毛損）": "580,000",
            "營業利益（損失）": "450,000",
            "本期淨利（淨損）": "390,000",
            "基本每股盈餘（元）": "15.20",
        },
        "balance_sheet": {
            "公司代號": "2330",
            "年度": "114",
            "季別": "2",
            "現金及約當現金": "600,000",
            "存貨": "200,000",
            "流動資產": "1,200,000",
            "資產總額": "3,000,000",
            "流動負債": "500,000",
            "負債總額": "1,100,000",
            "權益總額": "1,900,000",
        },
        "monthly_revenue": {
            "公司代號": "2330",
            "資料年月": "11506",
            "營業收入-當月營收": "250,000",
            "營業收入-上月營收": "230,000",
            "營業收入-去年當月營收": "200,000",
            "營業收入-上月比較增減(%)": "8.70",
            "營業收入-去年同月增減(%)": "25.00",
        },
        "_errors": None,
    }

    statement = normalize_twse_bundle(profile(), bundle)
    assert statement.report_period == "2025Q2"
    assert statement.monthly_revenue_period == "2026-06"
    assert statement.revenue == 1000000
    assert statement.gross_profit == 580000
    assert statement.total_assets == 3000000
    assert statement.equity == 1900000
    assert statement.monthly_revenue == 250000
    assert all(source.status == "available" for source in statement.source_coverage)
