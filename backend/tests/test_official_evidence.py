from __future__ import annotations

from app.official_event_models import OfficialEvidenceSummary
from app.services.official_event_sources import (
    build_investor_conference_metadata,
    build_material_event_metadata,
    classify_material_event,
    investor_conference_query_url,
    material_event_query_url,
)
from app.services.official_evidence_service import OfficialEvidenceService


class EmptySnapshotRepository:
    def get_latest_snapshot(self, ticker: str):
        return None


class FakeSnapshot:
    def model_dump(self, mode: str = "json"):
        assert mode == "json"
        return {
            "ticker": "2330",
            "company_name": "台積電",
            "overall_severity": "normal",
            "summary": "測試 snapshot。",
            "sources": [
                {
                    "source_name": "MOPS 年度合併財報",
                    "source_url": "https://mops.twse.com.tw/",
                }
            ],
            "limitations": ["測試限制"],
        }


class SnapshotRepository:
    def get_latest_snapshot(self, ticker: str):
        assert ticker == "2330"
        return FakeSnapshot()


def test_official_query_urls_use_mops_entry_points() -> None:
    assert "t100sb07_1" in investor_conference_query_url("2330")
    assert "co_id=2330" in investor_conference_query_url("2330")
    assert "t05st01" in material_event_query_url("2330", year=2024)
    assert "year=2024" in material_event_query_url("2330", year=2024)


def test_investor_conference_metadata_is_subindustry_aware() -> None:
    records = build_investor_conference_metadata("3711")
    assert len(records) == 1
    record = records[0]
    assert record.company_name == "日月光投控"
    assert record.subindustry == "封裝測試"
    assert "operating_cash_flow" in record.related_metrics
    assert record.status == "metadata_only"
    assert record.source_url.startswith("https://mops.twse.com.tw/mops/web/t100sb07_1")


def test_material_event_classification_maps_to_financial_metrics() -> None:
    category, metrics, risk_related = classify_material_event("董事會決議擴產並提高資本支出")
    assert category == "capacity_or_capex"
    assert risk_related is True
    assert "capex_intensity" in metrics

    records = build_material_event_metadata("2454", year=2024, title="公司說明庫存去化與需求變化")
    assert records[0].category == "inventory_or_demand"
    assert "inventory_growth_yoy" in records[0].related_metrics


def test_official_evidence_aggregate_without_snapshot_keeps_event_layers() -> None:
    evidence = OfficialEvidenceService(repository=EmptySnapshotRepository()).build("2330")
    assert isinstance(evidence, OfficialEvidenceSummary)
    assert evidence.readiness == "needs_refresh"
    assert "investor_conference" in evidence.evidence_layers
    assert "material_event" in evidence.evidence_layers
    assert evidence.financial_snapshot is None
    assert any("尚未有最新財報 snapshot" in item for item in evidence.limitations)


def test_official_evidence_aggregate_with_snapshot_is_frontend_ready() -> None:
    evidence = OfficialEvidenceService(repository=SnapshotRepository()).build("2330")
    assert evidence.readiness == "ready_for_frontend_integration"
    assert "financial_snapshot" in evidence.evidence_layers
    assert evidence.financial_snapshot["overall_severity"] == "normal"
    assert len(evidence.sources) >= 3
    assert "年度財報 latest snapshot" in evidence.official_evidence_summary
