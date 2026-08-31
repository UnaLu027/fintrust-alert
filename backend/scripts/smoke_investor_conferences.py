from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.services.official_event_sources import build_investor_conference_metadata

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = BACKEND_ROOT / "data" / "demo-output" / "investor-conference-summary.json"


def build_payload(*, tickers: list[str], fetch_live: bool) -> dict[str, Any]:
    results = []
    failures = []
    for ticker in tickers:
        try:
            records = build_investor_conference_metadata(ticker, fetch_live=fetch_live)
            results.append(
                {
                    "ticker": ticker,
                    "record_count": len(records),
                    "records": [record.model_dump(mode="json") for record in records],
                    "status": "available" if any(record.status == "available" for record in records) else "metadata_only",
                    "document_links_found": [record.document_url for record in records if record.document_url],
                    "claim_count": sum(len(record.disclosure_claims) for record in records),
                }
            )
        except Exception as exc:  # pragma: no cover - live smoke diagnostic path
            failures.append(f"{ticker}: {exc}")
            results.append({"ticker": ticker, "status": "failed", "error": str(exc)})
    return {
        "phase": "phase4_investor_conference_content_mvp",
        "fetch_live": fetch_live,
        "teacher_alignment": [
            "年度財報之外，開始讀取法說會 metadata / HTML preview / 附件連結",
            "法說會只作為官方文字證據，不覆蓋 deterministic 財報規則結果",
            "Gemini 後續可針對 disclosure_claims 與財報指標做 evidence-grounded 摘要",
        ],
        "results": results,
        "failures": failures,
        "result": "PASS" if not failures else "WARN",
    }


def write_payload(payload: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 4 investor conference smoke.")
    parser.add_argument("--tickers", nargs="+", default=["2330", "2303", "2454", "3711"])
    parser.add_argument("--fetch-live", action="store_true", help="Attempt live MOPS HTML fetch. Default keeps metadata-only stable demo.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--no-output", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(tickers=[str(ticker) for ticker in args.tickers], fetch_live=args.fetch_live)
    if not args.no_output:
        output_path = write_payload(payload, args.output)
        payload["output_file"] = str(output_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
