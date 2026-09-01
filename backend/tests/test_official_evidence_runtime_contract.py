from pathlib import Path

from scripts.smoke_official_evidence import DEFAULT_OUTPUT_PATH


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_official_evidence_runtime_contract_mentions_all_layers() -> None:
    contract = (REPO_ROOT / "docs" / "integration-api-contract.md").read_text(encoding="utf-8")
    source_doc = (REPO_ROOT / "docs" / "official-evidence-sources-and-rules.md").read_text(encoding="utf-8")
    assert "official-evidence" in contract
    assert "法說會 metadata" in contract
    assert "重大訊息 metadata" in contract
    assert "Gemini" in contract
    assert "t100sb07_1" in source_doc
    assert "t05st01" in source_doc


def test_official_evidence_demo_output_path() -> None:
    assert DEFAULT_OUTPUT_PATH.name == "official-evidence-summary.json"
    assert "demo-output" in str(DEFAULT_OUTPUT_PATH)
