from datetime import datetime, timezone

from app.models import FinancialFact, VerificationVerdict
from app.services.claim_parser import extract_claim
from app.services.fact_repository import FinancialFactRepository
from app.services.verifier import verify_claim


def fact(
    period: str,
    value: float,
    *,
    ticker: str = "2454",
    company_name: str = "聯發科",
    subindustry: str = "IC 設計",
    metric: str = "revenue",
    unit: str = "百萬元",
) -> FinancialFact:
    return FinancialFact(
        ticker=ticker,
        company_name=company_name,
        semiconductor_subindustry=subindustry,
        metric=metric,
        period=period,
        value=value,
        unit=unit,
        statement_type="income_statement",
        source_kind="mvp_fixture",
        source_url="https://mops.twse.com.tw/",
        filed_at=datetime(2026, 7, 25, tzinfo=timezone.utc),
        statement_scope="consolidated",
        is_demo=True,
    )


def test_verification_contradicts_large_difference(tmp_path):
    repo = FinancialFactRepository(str(tmp_path / "facts.db"))
    repo.upsert_many([fact("2025FY", 590000), fact("2024FY", 530000)])
    claim = extract_claim("聯發科 2025 年全年營收年增 45%")
    result = verify_claim(claim, repo, tolerance_percentage_points=2)
    assert result.verdict == VerificationVerdict.CONTRADICTED
    assert round(result.evidence.calculated_value, 2) == 11.32
    assert round(result.difference, 2) == 33.68
    assert result.evidence.formula


def test_verification_reports_insufficient_evidence(tmp_path):
    repo = FinancialFactRepository(str(tmp_path / "facts.db"))
    claim = extract_claim("聯發科 2025 年全年營收年增 45%")
    result = verify_claim(claim, repo)
    assert result.verdict == VerificationVerdict.INSUFFICIENT_EVIDENCE


def test_yoy_decrease_uses_negative_expected_value(tmp_path):
    repo = FinancialFactRepository(str(tmp_path / "facts.db"))
    repo.upsert_many([fact("2025FY", 90), fact("2024FY", 100)])
    claim = extract_claim("聯發科 2025 年全年營收年減 10%")
    result = verify_claim(claim, repo, tolerance_percentage_points=0.1)
    assert result.verdict == VerificationVerdict.SUPPORTED
    assert result.evidence.calculated_value == -10
    assert result.difference == 0


def test_percentage_point_decrease_uses_signed_comparison(tmp_path):
    repo = FinancialFactRepository(str(tmp_path / "facts.db"))
    repo.upsert_many(
        [
            fact(
                "2025Q2",
                48,
                ticker="2330",
                company_name="台積電",
                subindustry="晶圓代工",
                metric="gross_margin",
                unit="%",
            ),
            fact(
                "2024Q2",
                53,
                ticker="2330",
                company_name="台積電",
                subindustry="晶圓代工",
                metric="gross_margin",
                unit="%",
            ),
        ]
    )
    claim = extract_claim("台積電 2025 年第 2 季毛利率較去年同期下降 5 個百分點")
    result = verify_claim(claim, repo, tolerance_percentage_points=0.1)
    assert result.verdict == VerificationVerdict.SUPPORTED
    assert result.evidence.calculated_value == -5
    assert result.difference == 0


def test_money_claim_is_converted_to_official_thousand_dollar_unit(tmp_path):
    repo = FinancialFactRepository(str(tmp_path / "facts.db"))
    repo.upsert_many(
        [
            fact(
                "2024FY",
                590_000_000,
                metric="revenue",
                unit="新台幣仟元",
            )
        ]
    )
    claim = extract_claim("聯發科 2024 年全年營收為 5900 億元")
    result = verify_claim(claim, repo, tolerance_percentage_points=0.1)
    assert result.verdict == VerificationVerdict.SUPPORTED
    assert result.difference == 0
