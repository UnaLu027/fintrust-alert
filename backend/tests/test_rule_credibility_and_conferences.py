from __future__ import annotations

import json
from pathlib import Path

from app.services.official_event_sources import (
    build_investor_conference_metadata,
    infer_official_claims,
    parse_investor_conference_html,
)

RULE_DIR = Path(__file__).resolve().parents[1] / "app" / "rules"
RULE_FILES = [
    "semiconductor_historical_rules.json",
    "foundry_historical_rules.json",
    "ic_design_historical_rules.json",
    "packaging_testing_historical_rules.json",
]


def test_every_historical_rule_has_credibility_metadata() -> None:
    for name in RULE_FILES:
        config = json.loads((RULE_DIR / name).read_text(encoding="utf-8"))
        for rule in config["rules"]:
            assert rule["evidence_basis"]
            assert rule["evidence_references"]
            assert rule["credibility_level"] in {
                "official_standard",
                "peer_reviewed_literature",
                "industry_theory",
                "company_history_heuristic",
                "mvp_heuristic",
            }
            assert rule["calibration_status"] in {
                "official_definition",
                "literature_supported_mvp_threshold",
                "company_history_threshold",
                "peer_baseline_pending",
                "mvp_threshold",
            }


def test_investor_conference_html_parser_extracts_links_topics_and_claims() -> None:
    html = """
    <html><body>
      <table>
        <tr><td>2026/08/12</td><td>台積電第二季法人說明會</td></tr>
      </table>
      <p>本次法說會說明資本支出、產能規劃、庫存去化與未來營收展望。</p>
      <a href="/server-java/t57sb01?doc=2330.pdf">法說會簡報 PDF</a>
    </body></html>
    """
    records = parse_investor_conference_html("2330", html, source_url="https://mops.twse.com.tw/mops/web/t100sb07_1?co_id=2330")
    assert records
    assert len(records) <= 3

    primary = records[0]
    assert primary.status == "available"
    assert primary.document_extract_status == "document_link_found"
    assert primary.document_url is not None
    assert "資本支出與產能規劃" in primary.extracted_topics
    assert "capex_intensity" in primary.related_metrics
    assert primary.disclosure_claims
    assert primary.conference_date == "2026-08-12"


def test_metadata_fallback_remains_stable_without_live_fetch() -> None:
    records = build_investor_conference_metadata("2454", fetch_live=False)
    assert records[0].status == "metadata_only"
    assert "rd_intensity" in records[0].related_metrics
    assert records[0].document_url is None


def test_official_claim_extraction_is_bounded_to_known_topics() -> None:
    claims = infer_official_claims(
        "公司提到研發投入、新產品 roadmap、庫存去化與 cash flow。",
        source_url="https://mops.twse.com.tw/mops/web/t100sb07_1?co_id=2454",
    )
    claim_types = {claim.claim_type for claim in claims}
    assert "rd_or_product" in claim_types
    assert "inventory_or_demand" in claim_types
    assert all(claim.confidence < 1 for claim in claims)
    assert all(claim.evidence_source.startswith("https://mops.twse.com.tw") for claim in claims)
