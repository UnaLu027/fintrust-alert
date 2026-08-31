from __future__ import annotations

from app.services import official_company_ir_sources as ir_sources
from app.services.official_company_ir_sources import build_official_ir_fallback_metadata


def test_blocked_official_ir_uses_seeded_search_index(monkeypatch) -> None:
    def blocked_fetch(url: str, *, timeout_seconds: float = 12.0) -> str:
        raise RuntimeError("HTTP Error 403: Forbidden")

    monkeypatch.setattr(ir_sources, "fetch_official_ir_html", blocked_fetch)

    records, debug = build_official_ir_fallback_metadata("2330")

    assert records
    assert debug["blocked_by_source"] is True
    assert debug["fallback_mode"] == "seeded_official_search_index_after_403"
    assert debug["available"] is True
    assert records[0].status == "available"
    assert records[0].source_name == "公司官方投資人關係網站（search-index fallback）"
    assert records[0].document_url
    assert records[0].document_extract_status == "document_link_found"
    assert records[0].disclosure_claims
    assert any("403 Forbidden" in item for item in records[0].limitations)


def test_live_official_ir_html_still_takes_priority(monkeypatch) -> None:
    html = """
    <html><body>
      <h1>MediaTek Investor Relations</h1>
      <a href="/investor-relations/download/presentation.pdf">Investor Conference Presentation Material</a>
      <p>Revenue outlook, demand, inventory and cash flow are discussed in the presentation.</p>
    </body></html>
    """

    def live_fetch(url: str, *, timeout_seconds: float = 12.0) -> str:
        return html

    monkeypatch.setattr(ir_sources, "fetch_official_ir_html", live_fetch)

    records, debug = build_official_ir_fallback_metadata("2454")

    assert records
    assert debug["blocked_by_source"] is False
    assert debug["fallback_mode"] == "live_html"
    assert records[0].status == "available"
    assert records[0].document_url
    assert records[0].source_name == "公司官方投資人關係網站"
