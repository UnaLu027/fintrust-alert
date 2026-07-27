from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterable

from app.historical_analysis_models import HistoricalPeriodRecord
from app.models import CompanyProfile

try:
    from twmops import FinancialFetcher
    from twmops.fetchers.financial import FinancialFetcherError
except ImportError:  # pragma: no cover - deployment dependency guard
    FinancialFetcher = None  # type: ignore[assignment]

    class FinancialFetcherError(Exception):
        pass


class MopsInlineXbrlError(RuntimeError):
    pass


MOPS_DOWNLOAD_TEMPLATE = (
    "https://mopsov.twse.com.tw/server-java/FileDownLoad"
    "?functionName=t164sb01&step=9&co_id={ticker}&year={roc_year}"
    "&season=4&report_id=C"
)

# Each entry contains preferred Chinese labels followed by stable IFRS/TWSE
# concept suffixes. Both are used because labels and taxonomy prefixes can vary
# by filing year while the economic meaning remains the same.
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "revenue": (
        "營業收入",
        "營業收入合計",
        "Revenue",
        "OperatingRevenue",
        "RevenueFromContractsWithCustomers",
    ),
    "gross_profit": (
        "營業毛利（毛損）",
        "營業毛利(毛損)",
        "營業毛利",
        "GrossProfitLoss",
    ),
    "operating_income": (
        "營業利益（損失）",
        "營業利益(損失)",
        "營業利益",
        "OperatingIncomeLoss",
    ),
    "net_income": (
        "本期淨利（淨損）",
        "本期淨利(淨損)",
        "本期淨利",
        "本期稅後淨利（淨損）",
        "稅後淨利",
        "ProfitLoss",
    ),
    "eps": (
        "基本每股盈餘（元）",
        "基本每股盈餘(元)",
        "基本每股盈餘",
        "BasicEarningsLossPerShare",
    ),
    "cash_and_cash_equivalents": (
        "現金及約當現金",
        "CashAndCashEquivalents",
    ),
    "inventory": ("存貨", "Inventories"),
    "current_assets": ("流動資產", "CurrentAssets"),
    "total_assets": ("資產總額", "資產合計", "Assets"),
    "current_liabilities": ("流動負債", "CurrentLiabilities"),
    "total_liabilities": ("負債總額", "負債合計", "Liabilities"),
    "equity": ("權益總額", "權益總計", "Equity"),
    "operating_cash_flow": (
        "營業活動之淨現金流入（流出）",
        "營業活動之淨現金流入(流出)",
        "營業活動之淨現金流量",
        "NetCashFlowsFromUsedInOperatingActivities",
    ),
    "investing_cash_flow": (
        "投資活動之淨現金流入（流出）",
        "投資活動之淨現金流入(流出)",
        "投資活動之淨現金流量",
        "NetCashFlowsFromUsedInInvestingActivities",
    ),
    "capital_expenditure": (
        "取得不動產、廠房及設備",
        "購置不動產、廠房及設備",
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "AcquisitionOfPropertyPlantAndEquipment",
    ),
    "research_and_development_expense": (
        "研究發展費用",
        "研究及發展費用",
        "研發費用",
        "ResearchAndDevelopmentExpense",
    ),
}

STATEMENT_TYPES = ("income_statement", "balance_sheet", "cash_flow")


def _normalized_token(value: Any) -> str:
    text = str(value or "").casefold()
    return re.sub(r"[\s\-_:：()（）,.，、/\\]", "", text)


def _item_value(item: Any, name: str) -> Any:
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)


def _match_score(concept: str, label: str, alias: str) -> int:
    normalized_alias = _normalized_token(alias)
    normalized_label = _normalized_token(label)
    normalized_concept = _normalized_token(concept.split(":")[-1])
    if normalized_label == normalized_alias:
        return 4
    if normalized_concept == normalized_alias:
        return 3
    if normalized_alias and normalized_alias in normalized_label:
        return 2
    if normalized_alias and normalized_concept.endswith(normalized_alias):
        return 1
    return 0


def _extract_value(items: Iterable[Any], aliases: tuple[str, ...]) -> tuple[float | None, str | None]:
    best: tuple[int, float, str] | None = None
    for item in items:
        raw_value = _item_value(item, "value")
        if raw_value is None:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        concept = str(_item_value(item, "type") or "")
        label = str(_item_value(item, "origin_name") or "")
        score = max((_match_score(concept, label, alias) for alias in aliases), default=0)
        if score == 0:
            continue
        match_name = label or concept
        if best is None or score > best[0]:
            best = (score, value, match_name)
    if best is None:
        return None, None
    return best[1], best[2]


def normalize_mops_annual_statement(
    profile: CompanyProfile,
    roc_year: int,
    items: Iterable[Any],
    *,
    source_url: str | None = None,
    warnings: list[str] | None = None,
) -> HistoricalPeriodRecord:
    item_list = list(items)
    values: dict[str, float | None] = {}
    concept_matches: dict[str, str] = {}
    found: list[str] = []
    missing: list[str] = []

    for canonical, aliases in FIELD_ALIASES.items():
        value, matched_name = _extract_value(item_list, aliases)
        values[canonical] = value
        if value is None:
            missing.append(canonical)
        else:
            found.append(canonical)
            if matched_name:
                concept_matches[canonical] = matched_name

    fiscal_year = roc_year + 1911
    record_warnings = list(warnings or [])
    core_found = sum(values[field] is not None for field in ("revenue", "total_assets", "net_income"))
    status = "available" if core_found >= 2 else "missing"
    if status == "missing":
        record_warnings.append(
            "MOPS iXBRL 已下載，但核心財報欄位不足，可能是 taxonomy mapping 尚未涵蓋該年度概念。"
        )

    return HistoricalPeriodRecord(
        ticker=profile.ticker,
        company_name=profile.name,
        subindustry=profile.subindustry,
        fiscal_year=fiscal_year,
        roc_year=roc_year,
        period=f"{fiscal_year}FY",
        source_url=source_url
        or MOPS_DOWNLOAD_TEMPLATE.format(ticker=profile.ticker, roc_year=roc_year),
        status=status,
        fields_found=found,
        fields_missing=missing,
        concept_matches=concept_matches,
        warnings=record_warnings,
        **values,
    )


class MopsInlineXbrlClient:
    """Fetch annual consolidated Inline XBRL filings from MOPS.

    The first integration deliberately uses Q4/annual filings only. This avoids
    treating year-to-date Q2/Q3 values as standalone quarterly performance.
    """

    def __init__(self, fetcher: Any | None = None) -> None:
        if fetcher is not None:
            self.fetcher = fetcher
        elif FinancialFetcher is None:
            raise MopsInlineXbrlError(
                "缺少 twmops 套件；請重新安裝 backend/requirements.txt。"
            )
        else:
            self.fetcher = FinancialFetcher()

    async def fetch_annual(self, profile: CompanyProfile, roc_year: int) -> HistoricalPeriodRecord:
        combined_items: list[Any] = []
        warnings: list[str] = []

        for statement_type in STATEMENT_TYPES:
            try:
                statement = await self.fetcher.get_simplified_statement_async(
                    stock_id=profile.ticker,
                    year=roc_year,
                    quarter=4,
                    statement_type=statement_type,
                )
                combined_items.extend(getattr(statement, "items", []))
            except FinancialFetcherError as exc:
                warnings.append(f"{statement_type} 取得失敗：{exc}")
            except Exception as exc:
                warnings.append(f"{statement_type} 下載或解析失敗：{exc}")

        if not combined_items:
            detail = "；".join(warnings) or "查無可解析的財報項目"
            raise MopsInlineXbrlError(detail)

        return normalize_mops_annual_statement(
            profile,
            roc_year,
            combined_items,
            warnings=warnings,
        )

    async def fetch_history(
        self,
        profile: CompanyProfile,
        *,
        years: int = 5,
        end_roc_year: int | None = None,
    ) -> list[HistoricalPeriodRecord]:
        if not 3 <= years <= 5:
            raise ValueError("MVP 歷史期間僅支援 3 至 5 年。")

        now = datetime.now(timezone.utc)
        latest_candidate = end_roc_year or (now.year - 1911 - 1)
        periods: list[HistoricalPeriodRecord] = []
        attempts = 0
        candidate = latest_candidate

        # Try at most two additional years so an annual filing not yet published
        # does not prevent returning the requested number of available periods.
        while (
            sum(period.status == "available" for period in periods) < years
            and attempts < years + 2
        ):
            attempts += 1
            try:
                record = await self.fetch_annual(profile, candidate)
                periods.append(record)
            except MopsInlineXbrlError as exc:
                fiscal_year = candidate + 1911
                periods.append(
                    HistoricalPeriodRecord(
                        ticker=profile.ticker,
                        company_name=profile.name,
                        subindustry=profile.subindustry,
                        fiscal_year=fiscal_year,
                        roc_year=candidate,
                        period=f"{fiscal_year}FY",
                        source_url=MOPS_DOWNLOAD_TEMPLATE.format(
                            ticker=profile.ticker,
                            roc_year=candidate,
                        ),
                        status="error",
                        warnings=[str(exc)],
                        fields_missing=list(FIELD_ALIASES),
                    )
                )
            candidate -= 1

        return sorted(periods, key=lambda record: record.fiscal_year)
