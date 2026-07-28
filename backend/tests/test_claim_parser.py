from app.models import ClaimDirection, ComparisonKind
from app.services.claim_parser import extract_claim


def test_extract_semiconductor_revenue_yoy_claim():
    claim = extract_claim("聯發科 2025 年全年營收年增 45%")
    assert claim.ticker == "2454"
    assert claim.semiconductor_subindustry == "IC 設計"
    assert claim.metric == "revenue"
    assert claim.period == "2025FY"
    assert claim.comparison_period == "2024FY"
    assert claim.comparison_kind == ComparisonKind.YOY
    assert claim.direction == ClaimDirection.INCREASE
    assert claim.claimed_change_percent == 45


def test_does_not_guess_ambiguous_period():
    claim = extract_claim("台積電今年營收大增")
    assert claim.period is None
    assert "period" in claim.missing_fields


def test_extract_percentage_point_comparison_period():
    claim = extract_claim("台積電 2025 年第 2 季毛利率較去年同期下降 5 個百分點")
    assert claim.metric == "gross_margin"
    assert claim.period == "2025Q2"
    assert claim.comparison_period == "2024Q2"
    assert claim.claimed_percentage_points == 5


def test_amount_does_not_use_year_as_claimed_value():
    claim = extract_claim("聯發科 2025 年全年營收為 5900 億元")
    assert claim.claimed_value == 5900
    assert claim.unit == "億"


def test_extract_cash_flow_and_capex_intensity_metrics():
    cash = extract_claim("台積電 2024 年全年營業現金流為 1.8 兆元")
    capex = extract_claim("台積電 2024 年全年資本支出占營收比為 32%")
    assert cash.metric == "operating_cash_flow"
    assert cash.claimed_value == 1.8
    assert cash.unit == "兆"
    assert capex.metric == "capex_intensity"
    assert capex.claimed_value == 32
    assert capex.unit == "%"


def test_extract_research_and_inventory_metrics():
    rd = extract_claim("聯發科 2024 年全年研發強度為 24%")
    inventory = extract_claim("日月光投控 2024 年全年存貨年增率為 8%")
    assert rd.metric == "rd_intensity"
    assert inventory.metric == "inventory_growth_yoy"
