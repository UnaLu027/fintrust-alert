from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_official_evidence_contract_mentions_teacher_required_layers() -> None:
    contract = (REPO_ROOT / "docs" / "integration-api-contract.md").read_text(encoding="utf-8")
    source_doc = (REPO_ROOT / "docs" / "official-evidence-sources-and-rules.md").read_text(encoding="utf-8")

    assert "official-evidence" in contract
    assert "法說會 metadata" in contract
    assert "重大訊息 metadata" in contract
    assert "Gemini" in contract
    assert "t100sb07_1" in source_doc
    assert "t05st01" in source_doc
    assert "FOUNDRY_CAPEX_MARGIN_001" in source_doc
    assert "ICDESIGN_RD_INVENTORY_001" in source_doc
    assert "PACKAGING_WORKING_CAPITAL_001" in source_doc
