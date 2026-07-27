import asyncio
from types import SimpleNamespace

import pytest

from app.services.company_registry import get_company
from app.services.mops_inline_xbrl import (
    MopsInlineXbrlClient,
    normalize_mops_annual_package,
)


@pytest.fixture
def tsmc():
    company = get_company("2330")
    assert company is not None
    return company


def context(
    context_id: str,
    *,
    start: str | None = None,
    end: str | None = None,
    instant: str | None = None,
):
    return SimpleNamespace(
        context_id=context_id,
        period_start=start,
        period_end=end,
        instant=instant,
    )


def fact(concept: str, value: float, context_ref: str):
    return SimpleNamespace(
        concept=concept,
        value=str(value),
        context_ref=context_ref,
    )


def annual_package(roc_year: int, revenue: float = 2_800_000):
    fiscal_year = roc_year + 1911
    current_duration = "current_duration"
    prior_duration = "prior_duration"
    current_instant = "current_instant"
    prior_instant = "prior_instant"
    contexts = {
        current_duration: context(
            current_duration,
            start=f"{fiscal_year}-01-01",
            end=f"{fiscal_year}-12-31",
        ),
        prior_duration: context(
            prior_duration,
            start=f"{fiscal_year - 1}-01-01",
            end=f"{fiscal_year - 1}-12-31",
        ),
        current_instant: context(current_instant, instant=f"{fiscal_year}-12-31"),
        prior_instant: context(prior_instant, instant=f"{fiscal_year - 1}-12-31"),
    }
    facts = [
        fact("Revenue", revenue, current_duration),
        fact("Revenue", 99, prior_duration),
        fact("GrossProfitLoss", revenue * 0.5, current_duration),
        fact("OperatingIncomeLoss", revenue * 0.4, current_duration),
        fact("ProfitLoss", revenue * 0.3, current_duration),
        fact("Assets", revenue * 2, current_instant),
        fact("Assets", 88, prior_instant),
        fact("Liabilities", revenue * 0.6, current_instant),
        fact("Equity", revenue * 1.4, current_instant),
        fact("NetCashFlowsFromUsedInOperatingActivities", revenue * 0.35, current_duration),
        fact("PaymentsToAcquirePropertyPlantAndEquipment", -revenue * 0.2, current_duration),
    ]
    labels = {
        "Revenue": "營業收入",
        "GrossProfitLoss": "營業毛利（毛損）",
        "OperatingIncomeLoss": "營業利益（損失）",
        "ProfitLoss": "本期淨利（淨損）",
        "Assets": "資產總額",
        "Liabilities": "負債總額",
        "Equity": "權益總額",
        "NetCashFlowsFromUsedInOperatingActivities": "營業活動之淨現金流入（流出）",
        "PaymentsToAcquirePropertyPlantAndEquipment": "取得不動產、廠房及設備",
    }
    return SimpleNamespace(facts=facts, contexts=contexts, labels=labels)


def test_normalize_package_uses_current_year_context_not_comparative_fact(tsmc):
    record = normalize_mops_annual_package(tsmc, 114, annual_package(114))

    assert record.status == "available"
    assert record.period == "2025FY"
    assert record.revenue == 2_800_000
    assert record.total_assets == 5_600_000
    assert record.operating_cash_flow == pytest.approx(980_000)
    assert record.capital_expenditure == pytest.approx(-560_000)
    assert record.revenue != 99
    assert record.total_assets != 88
    assert "revenue" in record.concept_matches
    assert "year=2025" in record.source_url


class FakeXbrlClient:
    def __init__(self):
        self.calls: list[tuple[str, int, int, str]] = []

    async def download_xbrl_async(
        self,
        stock_id: str,
        year: int,
        quarter: int,
        report_type: str = "C",
    ) -> bytes:
        self.calls.append((stock_id, year, quarter, report_type))
        if year == 114:
            raise RuntimeError("annual filing not available")
        return str(year).encode()


class FakeParser:
    def parse(self, content: bytes, stock_id: str, year: int, quarter: int):
        assert int(content.decode()) == year
        return annual_package(year, revenue=year * 1000)


def test_fetch_history_keeps_error_period_but_collects_requested_available_years(tsmc):
    xbrl_client = FakeXbrlClient()
    client = MopsInlineXbrlClient(
        xbrl_client=xbrl_client,
        parser=FakeParser(),
        require_arelle=False,
        cache_enabled=False,
    )

    periods = asyncio.run(client.fetch_history(tsmc, years=3, end_roc_year=114))

    available = [period for period in periods if period.status == "available"]
    errors = [period for period in periods if period.status == "error"]
    assert len(available) == 3
    assert len(errors) == 1
    assert errors[0].period == "2025FY"
    assert {period.period for period in available} == {"2022FY", "2023FY", "2024FY"}
    assert len(xbrl_client.calls) == 4
    assert all(call[3] == "C" for call in xbrl_client.calls)


def test_fetch_annual_reuses_raw_ixbrl_cache(tsmc, tmp_path):
    xbrl_client = FakeXbrlClient()
    client = MopsInlineXbrlClient(
        xbrl_client=xbrl_client,
        parser=FakeParser(),
        require_arelle=False,
        cache_dir=tmp_path,
        cache_ttl_hours=24,
    )

    first = asyncio.run(client.fetch_annual(tsmc, 113))
    second = asyncio.run(client.fetch_annual(tsmc, 113))

    assert first.revenue == second.revenue
    assert len(xbrl_client.calls) == 1
    assert (tmp_path / "2330_113_Q4_C.ixbrl").exists()
