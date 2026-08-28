from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_fintrust_client_module():
    module_path = REPO_ROOT / "integrations" / "flask" / "fintrust_client.py"
    spec = importlib.util.spec_from_file_location("integration_fintrust_client", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses needs the dynamically-loaded module to exist in sys.modules
    # while class annotations are processed.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_fintrust_client_builds_latest_snapshot_request() -> None:
    module = load_fintrust_client_module()
    captured: dict[str, Any] = {}

    def fake_opener(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        return FakeResponse({"ticker": "2330", "overall_severity": "normal"})

    client = module.FinTrustClient(
        base_url="http://127.0.0.1:8000/",
        timeout_seconds=7.5,
        opener=fake_opener,
    )

    payload = client.latest_analysis("2330")

    assert payload == {"ticker": "2330", "overall_severity": "normal"}
    assert captured["url"] == "http://127.0.0.1:8000/api/v1/financial/companies/2330/analysis/latest"
    assert captured["method"] == "GET"
    assert captured["timeout"] == 7.5
    assert captured["headers"]["Accept"] == "application/json"


def test_fintrust_client_refresh_sends_server_side_ingestion_token() -> None:
    module = load_fintrust_client_module()
    captured: dict[str, Any] = {}

    def fake_opener(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["headers"] = dict(request.header_items())
        return FakeResponse({"status": "completed"})

    client = module.FinTrustClient(
        base_url="https://fintrust-api.example.run.app",
        ingestion_token="server-only-token",
        opener=fake_opener,
    )

    payload = client.refresh_company("2330", years=3, end_year=2024, trigger="manual")

    assert payload == {"status": "completed"}
    assert captured["method"] == "POST"
    assert captured["url"].startswith(
        "https://fintrust-api.example.run.app/api/v1/financial/admin/companies/2330/refresh?"
    )
    assert "years=3" in captured["url"]
    assert "end_year=2024" in captured["url"]
    assert "source_mode=official" in captured["url"]
    assert captured["headers"]["X-ingestion-token"] == "server-only-token"


def test_integration_contract_mentions_teacher_requested_sources() -> None:
    contract = (REPO_ROOT / "docs" / "integration-api-contract.md").read_text(encoding="utf-8")
    plan = (REPO_ROOT / "docs" / "teacher-aligned-development-plan.md").read_text(encoding="utf-8")
    assert "統一介面" in contract
    assert "法說會" in contract
    assert "重大訊息" in contract
    assert "MOPS" in contract
    assert "OpenAI" in plan
    assert "封裝測試" in plan


def test_flask_adapter_files_are_ready_to_copy() -> None:
    required_files = [
        REPO_ROOT / "integrations" / "flask" / "fintrust_client.py",
        REPO_ROOT / "integrations" / "flask" / "financial_routes.py",
        REPO_ROOT / "integrations" / "flask" / "templates" / "_financial_evidence_card.html",
        REPO_ROOT / "integrations" / "flask" / "static" / "financial-evidence.js",
        REPO_ROOT / "integrations" / "flask" / ".env.integration.example",
        REPO_ROOT / "integrations" / "flask" / "README.md",
    ]
    for file_path in required_files:
        assert file_path.exists(), file_path

    readme = (REPO_ROOT / "integrations" / "flask" / "README.md").read_text(encoding="utf-8")
    assert "Flask" in readme
    assert "FastAPI" in readme
    assert "analysis/latest" in readme
