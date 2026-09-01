import pytest

from app.models import VerificationVerdict
from app.services.analysis_repository import SqliteAnalysisRepository
from app.services.claim_parser import extract_claim
from app.services.ingestion_pipeline import FinancialIngestionPipeline
from app.services.pipeline_evidence_repository import PipelineEvidenceRepository
from app.services.verifier import verify_claim


@pytest.mark.asyncio
async def test_pipeline_facts_feed_claim_verifier_and_preserve_demo_provenance(tmp_path):
    repository = SqliteAnalysisRepository(str(tmp_path / "pipeline.sqlite3"))
    result = await FinancialIngestionPipeline(repository=repository).refresh_company(
        "2330",
        years=3,
        end_year=2024,
        trigger="demo",
        source_mode="demo_fixture",
    )

    assert result.status == "completed"
    current = repository.get_fact("2330", "revenue", "2024FY")
    previous = repository.get_fact("2330", "revenue", "2023FY")
    assert current is not None
    assert previous is not None
    assert current.is_demo is True
    assert current.source_kind == "mvp_fixture"

    claim = extract_claim("台積電 2024 年全年營收年增 10%")
    verification = verify_claim(claim, repository, tolerance_percentage_points=2)
    assert verification.verdict != VerificationVerdict.INSUFFICIENT_EVIDENCE
    assert verification.evidence is not None
    assert verification.evidence.is_demo is True


@pytest.mark.asyncio
async def test_derived_ratio_claim_uses_calculated_pipeline_metric(tmp_path):
    repository = SqliteAnalysisRepository(str(tmp_path / "pipeline.sqlite3"))
    await FinancialIngestionPipeline(repository=repository).refresh_company(
        "2330", years=3, end_year=2024, trigger="demo", source_mode="demo_fixture"
    )
    evidence_repository = PipelineEvidenceRepository(repository)

    claim = extract_claim("台積電 2024 年全年毛利率為 55%")
    verification = verify_claim(claim, evidence_repository, tolerance_percentage_points=2)

    assert verification.verdict != VerificationVerdict.INSUFFICIENT_EVIDENCE
    assert verification.evidence is not None
    assert verification.evidence.metric == "gross_margin"
    assert verification.evidence.is_demo is True


@pytest.mark.asyncio
async def test_metrics_can_be_filtered_to_latest_analysis_run(tmp_path):
    repository = SqliteAnalysisRepository(str(tmp_path / "pipeline.sqlite3"))
    pipeline = FinancialIngestionPipeline(repository=repository)
    first = await pipeline.refresh_company(
        "2330", years=3, end_year=2024, trigger="demo", source_mode="demo_fixture"
    )
    second = await pipeline.refresh_company(
        "2330", years=3, end_year=2024, trigger="demo", source_mode="demo_fixture"
    )

    assert first.run_id != second.run_id
    rows = repository.list_metrics("2330", limit=1000, run_id=second.run_id)
    assert rows
    assert {row["run_id"] for row in rows} == {second.run_id}
