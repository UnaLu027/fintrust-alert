from __future__ import annotations

import argparse
import asyncio
import json

from app.services.company_registry import get_company
from app.services.robust_mops_inline_xbrl import RobustMopsInlineXbrlClient


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect live/cached MOPS iXBRL concepts, labels and contexts for mapping gaps."
    )
    parser.add_argument("--ticker", default="2330")
    parser.add_argument("--roc-year", type=int, default=113)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    profile = get_company(args.ticker)
    if profile is None:
        raise SystemExit(f"Ticker {args.ticker} is not in the semiconductor registry.")

    payload = await RobustMopsInlineXbrlClient().diagnose_annual(profile, args.roc_year)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    print(rendered)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.write("\n")
        print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
