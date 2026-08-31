from pathlib import Path

from scripts import smoke_official_evidence
from scripts.smoke_official_evidence import DEFAULT_OUTPUT_PATH


def test_official_evidence_smoke_default_output_path_is_demo_artifact() -> None:
    assert DEFAULT_OUTPUT_PATH.name == "official-evidence-summary.json"
    assert "demo-output" in str(DEFAULT_OUTPUT_PATH)


def test_official_evidence_smoke_uses_repository_for_snapshot(monkeypatch, tmp_path: Path) -> None:
    repository = object()
    captured = {}

    class FakeEvidence:
        def model_dump(self, mode: str = "json"):
            assert mode == "json"
            return {
                "ticker": "2330",
                "financial_snapshot": {"overall_severity": "normal"},
                "readiness": "ready_for_frontend_integration",
            }

    class FakeOfficialEvidenceService:
        def __init__(self, *, repository):
            captured["repository"] = repository

        def build(self, ticker: str, *, material_event_year: int):
            captured["ticker"] = ticker
            captured["material_event_year"] = material_event_year
            return FakeEvidence()

    monkeypatch.setattr(smoke_official_evidence, "build_analysis_repository", lambda: repository)
    monkeypatch.setattr(smoke_official_evidence, "OfficialEvidenceService", FakeOfficialEvidenceService)

    output = tmp_path / "official-evidence-summary.json"
    smoke_official_evidence.main(["--ticker", "2330", "--material-event-year", "2024", "--output", str(output)])

    assert captured == {
        "repository": repository,
        "ticker": "2330",
        "material_event_year": 2024,
    }
    written = output.read_text(encoding="utf-8")
    assert '"financial_snapshot_present": true' in written
    assert '"repository_backend": "unknown"' in written
