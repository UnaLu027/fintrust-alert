from __future__ import annotations

import pytest

from app.services.analysis_repository import SqliteAnalysisRepository
from app.services.ingestion_pipeline import FinancialIngestionPipeline


@pytest.mark.asyncio
async def test_demo_fixture_pipeline_persists_snapshot_and_subindustry_rules(tmp_path):
    repository = SqliteAnalysisRepository(str(tmp_path / "demo.sqlite3"))
    pipeline = FinancialIngestionPipeline(repository=repository)

    result = await pipeline.refresh_company(
        "2330",
        years=3,
        end_year=2024,
        trigger="demo",
        source_mode="demo_fixture",
    )

    assert result.status == "completed"
    assert result.source_mode == "demo_fixture"
    assert result.persistence.filings == 3
    assert result.persistence.facts > 0
    assert result.persistence.metrics > 0
    assert result.persistence.rule_results > 0
    assert result.persistence.snapshots == 1

    snapshot = repository.get_latest_snapshot("2330")
    assert snapshot is not None
    assert snapshot.subindustry == "晶圓代工"
    assert snapshot.analysis_run_id == result.run_id
    assert any("DEMO FIXTURE" in text for text in snapshot.limitations)
    assert any(card.rule_scope == "foundry" for card in snapshot.rule_cards)
    assert any(card.code == "capex_intensity" for card in snapshot.key_metrics)


@pytest.mark.asyncio
async def test_demo_fixture_pipeline_dispatches_ic_design_rules(tmp_path):
    repository = SqliteAnalysisRepository(str(tmp_path / "demo-ic.sqlite3"))
    result = await FinancialIngestionPipeline(repository=repository).refresh_company(
        "2454",
        years=3,
        end_year=2024,
        trigger="demo",
        source_mode="demo_fixture",
    )

    assert result.status == "completed"
    assert result.snapshot is not None
    assert any(card.rule_scope == "ic_design" for card in result.snapshot.rule_cards)
