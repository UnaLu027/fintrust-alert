from datetime import datetime, timezone

from app.models import FinancialFact, VerificationVerdict
from app.services.claim_parser import extract_claim
from app.services.fact_repository import FinancialFactRepository
from app.services.verifier import verify_claim


def fact(period: str, value: float) -> FinancialFact:
    return FinancialFact(
        ticker="2454",
        company_name="聯發科",
        semiconductor_subindustry="IC 設計",
        metric="revenue",
        period=period,
        value=value,
        unit="百萬元",
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
