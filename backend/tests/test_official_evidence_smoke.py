from scripts.smoke_official_evidence import DEFAULT_OUTPUT_PATH


def test_official_evidence_smoke_default_output_path_is_demo_artifact() -> None:
    assert DEFAULT_OUTPUT_PATH.name == "official-evidence-summary.json"
    assert "demo-output" in str(DEFAULT_OUTPUT_PATH)
