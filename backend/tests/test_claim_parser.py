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
