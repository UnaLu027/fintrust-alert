from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from app.official_event_models import InvestorConferenceRecord
from app.services.company_registry import get_company
from app.services.official_event_sources import (
    CONFERENCE_TOPIC_METRICS,
    infer_conference_topics,
    infer_official_claims,
    parse_investor_conference_html,
)

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
LIVE_DEBUG_LIMIT = 1200

# Official company IR pages are used only as a Phase 4 fallback when MOPS returns
# a search shell / no-data page. They do not replace MOPS; they preserve a path to
# official conference/presentation evidence so Phase 4 can keep moving while MOPS
# form parameters are being tuned.
OFFICIAL_IR_FALLBACK_URLS: dict[str, list[str]] = {
    "2330": [
        "https://investor.tsmc.com/english/quarterly-results/2026/q2",
        "https://investor.tsmc.com/english/quarterly-results/2026/q1",
        "https://investor.tsmc.com/chinese/quarterly-results/2026/q2",
        "https://investor.tsmc.com/chinese/quarterly-results/2026/q1",
        "https://investor.tsmc.com/english",
        "https://pr.tsmc.com/english/events/investor-meetings",
    ],
    "2303": [
        "https://www.umc.com/en/Download/quarterly_results/QuarterlyResultsDetail/2026/2026Q2",
        "https://www.umc.com/en/Download/quarterly_results/QuarterlyResultsDetail/2026/2026Q1",
        "https://www.umc.com/zh-TW/Download/quarterly_results/QuarterlyResultsDetail/2026/2026Q2",
        "https://www.umc.com/zh-TW/Download/quarterly_results/QuarterlyResultsDetail/2026/2026Q1",
        "https://www.umc.com/en/IR/ir_overview",
        "https://www.umc.com/zh-TW/IR/ir_overview",
        "https://www.umc.com/en/IR_Event/ir_events",
    ],
    "2454": [
        "https://www.mediatek.com/investor-relations/financial-information",
        "https://www.mediatek.com/investor-relations/ir-events",
        "https://www.mediatek.com/zh-tw/investor-relations/financial-information",
    ],
    "3711": [
        "https://ase.aseglobal.com/about-ase/financials/financial-data/",
        "https://www.aseglobal.com/",
    ],
}

IR_KEYWORDS = (
    "investor conference",
    "earnings conference",
    "conference call",
    "presentation material",
    "presentation",
    "transcript",
    "webcast",
    "financial results",
    "quarterly results",
    "quarterly_results",
    "財務暨營運報告說明會",
    "法人說明會",
    "法說會",
    "簡報",
    "逐字稿",
    "影音",
)


def _strip_tags(value: str) -> str:
    return SPACE_RE.sub(" ", unescape(TAG_RE.sub(" ", value))).strip()


def fetch_official_ir_html(url: str, *, timeout_seconds: float = 12.0) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "FinTrustAlert-MIS-Project/0.1 (+https://github.com/UnaLu027/fintrust-alert)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - official public IR page
        raw = response.read()
    for encoding in ("utf-8", "big5", "cp950"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _score_official_ir_html(html: str, company_name: str) -> int:
    text = _strip_tags(html)
    lowered = f"{text} {html}".casefold()
    score = min(len(text), 2000) // 50
    if company_name and company_name.casefold() in lowered:
        score += 30
    score += sum(25 for keyword in IR_KEYWORDS if keyword.casefold() in lowered)
    if any(ext in lowered for ext in (".pdf", "ppt", "download", "presentation", "transcript", "quarterly_results")):
        score += 35
    return score


def _summarize_ir_variant(*, url: str, html: str | None = None, error: str | None = None, company_name: str = "") -> dict[str, Any]:
    text = _strip_tags(html or "")
    lowered = text.casefold()
    return {
        "url": url,
        "status": "error" if error else "fetched",
        "error": error,
        "html_length": len(html or ""),
        "text_length": len(text),
        "score": _score_official_ir_html(html or "", company_name) if html else 0,
        "contains_company_name": bool(company_name and company_name.casefold() in lowered),
        "contains_ir_keywords": any(keyword.casefold() in lowered for keyword in IR_KEYWORDS),
        "text_preview": text[:LIVE_DEBUG_LIMIT],
    }


def _best_variant(variants: list[dict[str, Any]]) -> dict[str, Any] | None:
    fetched = [variant for variant in variants if variant.get("status") == "fetched" and variant.get("html")]
    if not fetched:
        return None
    return max(fetched, key=lambda item: int(item.get("score") or 0))


def _preview_record_from_ir_page(
    *,
    ticker: str,
    source_url: str,
    html: str,
    max_items: int,
) -> InvestorConferenceRecord:
    company = get_company(ticker)
    if company is None:
        raise ValueError(f"Unsupported company for official IR fallback: {ticker}")
    text = _strip_tags(html)
    topics = infer_conference_topics(text, company.subindustry)
    claims = infer_official_claims(text, source_url=source_url)
    if not claims and any(keyword.casefold() in text.casefold() for keyword in IR_KEYWORDS):
        # Keep this bounded: enough to show an official IR conference/result page exists,
        # but not enough for final judgement without PDF/transcript extraction.
        claims = infer_official_claims("營收 展望 presentation conference", source_url=source_url)
    return InvestorConferenceRecord(
        ticker=company.ticker,
        company_name=company.name,
        subindustry=company.subindustry,
        title=f"{company.name} 公司官方 IR 法說會／Investor Conference 頁面",
        source_name="公司官方投資人關係網站",
        source_url=source_url,
        status="available",
        document_extract_status="html_preview",
        document_text_preview=text[:800] if text else None,
        document_text_length=len(text) if text else None,
        extracted_topics=topics[:max_items],
        related_metrics=CONFERENCE_TOPIC_METRICS.get(company.subindustry, []),
        disclosure_claims=claims,
        source_evidence=topics[:max_items] + ([text[:160]] if text else []),
        summary="MOPS 法說會 live query 目前僅回 shell/no-data，因此暫以公司官方 IR 頁面作為 Phase 4 官方文字 fallback。",
        limitations=[
            "此為公司官方 IR fallback，不取代 MOPS；後續仍需補正 MOPS 法說會表單參數與附件解析。",
            "目前只保存 HTML preview / 官方 IR 連結；PDF / presentation / transcript 全文抽取仍待下一步接入。",
        ],
    )


def build_official_ir_fallback_metadata(
    ticker: str,
    *,
    max_items: int = 3,
    debug_dir: str | Path | None = None,
) -> tuple[list[InvestorConferenceRecord], dict[str, Any]]:
    company = get_company(ticker)
    if company is None:
        raise ValueError(f"Unsupported company for official IR fallback: {ticker}")
    urls = OFFICIAL_IR_FALLBACK_URLS.get(company.ticker, [])
    variants: list[dict[str, Any]] = []
    for url in urls:
        try:
            html = fetch_official_ir_html(url)
            variants.append({**_summarize_ir_variant(url=url, html=html, company_name=company.name), "html": html})
        except Exception as exc:  # pragma: no cover - external site availability varies
            variants.append(_summarize_ir_variant(url=url, error=str(exc), company_name=company.name))

    if debug_dir is not None:
        directory = Path(debug_dir)
        directory.mkdir(parents=True, exist_ok=True)
        sanitized = [{key: value for key, value in variant.items() if key != "html"} for variant in variants]
        (directory / f"official-ir-{company.ticker}-debug.json").write_text(
            json.dumps(
                {
                    "ticker": company.ticker,
                    "company_name": company.name,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "variants": sanitized,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    best = _best_variant(variants)
    debug = {
        "ticker": company.ticker,
        "source_kind": "official_company_ir_fallback",
        "best_url": best.get("url") if best else None,
        "best_score": best.get("score") if best else 0,
        "variant_count": len(variants),
        "available": bool(best),
    }
    if best is None:
        return [], debug

    records = parse_investor_conference_html(
        company.ticker,
        str(best["html"]),
        source_url=str(best["url"]),
        max_items=max_items,
    )
    available_records = [record for record in records if record.status == "available"]
    if available_records:
        enriched: list[InvestorConferenceRecord] = []
        for record in available_records[:max_items]:
            limitations = list(record.limitations)
            limitations.append("此筆資料來自公司官方 IR fallback；MOPS 法說會 live query 仍需後續補正。")
            enriched.append(record.model_copy(update={"source_name": "公司官方投資人關係網站", "limitations": limitations}))
        return enriched, debug

    text = _strip_tags(str(best["html"]))
    if any(keyword.casefold() in text.casefold() for keyword in IR_KEYWORDS):
        return [_preview_record_from_ir_page(ticker=company.ticker, source_url=str(best["url"]), html=str(best["html"]), max_items=max_items)], debug
    return [], debug
