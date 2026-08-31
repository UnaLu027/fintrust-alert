from __future__ import annotations

import io
from email.message import Message
from urllib.error import HTTPError
from urllib.request import Request

from app.official_event_models import InvestorConferenceRecord, OfficialDocumentExtractionRequest
from app.services.official_document_extraction import (
    OfficialDocumentExtractionService,
    enrich_conferences_with_document_extraction,
)
from app.services.official_evidence_cards import OfficialEvidenceCardBuilder


class FakeResponse:
    def __init__(self, body: bytes, *, content_type: str = "text/html; charset=utf-8", status: int = 200, url: str = "https://example.com/doc") -> None:
        self._body = body
        self.status = status
        self.url = url
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_html_document_extraction_maps_claims_and_metrics() -> None:
    def opener(_request: Request, _timeout: float):
        html = """
        <html><body>
          <h1>Investor conference presentation</h1>
          <p>公司說明營收展望、資本支出、產能規劃與庫存去化。</p>
        </body></html>
        """
        return FakeResponse(html.encode("utf-8"), url="https://example.com/ir.html")

    result = OfficialDocumentExtractionService(opener=opener).extract(
        OfficialDocumentExtractionRequest(
            ticker="2454",
            document_url="https://example.com/ir.html",
            source_url="https://example.com/ir",
            document_title="Investor conference presentation",
        )
    )

    assert result.status == "available"
    assert result.extract_status == "text_extracted"
    assert result.text_preview is not None
    assert "營收展望" in result.text_preview
    assert result.disclosure_claims
    assert "rd_intensity" in result.related_metrics


def test_blocked_document_download_is_explicit_not_silent_failure() -> None:
    def opener(request: Request, _timeout: float):
        raise HTTPError(request.full_url, 403, "Forbidden", hdrs=None, fp=io.BytesIO(b""))

    result = OfficialDocumentExtractionService(opener=opener).extract(
        OfficialDocumentExtractionRequest(
            ticker="2330",
            document_url="https://investor.tsmc.com/english/quarterly-results/2026/q2",
            document_title="TSMC quarterly results",
        )
    )

    assert result.status == "blocked_by_source"
    assert result.extract_status == "blocked_by_source"
    assert result.http_status == 403
    assert result.error
    assert any("官方文件下載未成功" in item for item in result.limitations)


def test_enrich_conferences_preserves_record_and_adds_extraction() -> None:
    def opener(_request: Request, _timeout: float):
        return FakeResponse(
            b"<html><body>presentation revenue outlook inventory demand cash flow</body></html>",
            url="https://example.com/presentation.html",
        )

    record = InvestorConferenceRecord(
        ticker="3711",
        company_name="日月光投控",
        subindustry="封裝測試",
        title="Quarterly results presentation",
        source_name="公司官方投資人關係網站",
        source_url="https://example.com/ir",
        document_url="https://example.com/presentation.html",
        status="available",
        document_extract_status="document_link_found",
        related_metrics=["inventory_growth_yoy"],
    )

    enriched, results, summary = enrich_conferences_with_document_extraction(
        [record],
        service=OfficialDocumentExtractionService(opener=opener),
    )

    assert len(results) == 1
    assert enriched[0].document_extract_status == "text_extracted"
    assert enriched[0].document_text_preview
    assert enriched[0].document_extractions
    assert summary["text_extracted_count"] == 1


class EmptyRepository:
    def get_latest_snapshot(self, ticker: str):
        assert ticker == "2330"
        return None


def test_official_evidence_card_degrades_without_snapshot() -> None:
    card = OfficialEvidenceCardBuilder(repository=EmptyRepository()).build("2330")
    assert card.schema_version == "frontend-official-evidence-card-1.0.0"
    assert card.ticker == "2330"
    assert card.evidence_readiness == "needs_refresh"
    assert card.source_status["financial_snapshot_present"] is False
    assert "limitations" in card.model_dump(mode="json")
