import asyncio
from types import SimpleNamespace

import pytest

from app.services.company_registry import get_company
from app.services.mops_inline_xbrl import (
    MopsInlineXbrlClient,
    normalize_mops_annual_statement,
)


@pytest.fixture
def tsmc():
    company = get_company("2330")
    assert company is not None
    return company


def item(concept: str, label: str, value: float):
    return {
        "type": concept,
        "origin_name": label,
        "value": value,
    }


def test_normalize_mops_annual_statement_maps_core_and_cash_flow_fields(tsmc):
    record = normalize_mops_annual_statement(
        tsmc,
        114,
        [
            item("tifrs-fr1:Revenue", "營業收入", 2_800_000),
            item("tifrs-fr1:GrossProfitLoss", "營業毛利（毛損）", 1_500_000),
            item("tifrs-fr1:OperatingIncomeLoss", "營業利益（損失）", 1_200_000),
            item("tifrs-fr1:ProfitLoss", "本期淨利（淨損）", 1_000_000),
            item("tifrs-fr1:Assets", "資產總額", 6_000_000),
            item("tifrs-fr1:Liabilities", "負債總額", 2_000_000),
            item("tifrs-fr1:Equity", "權益總額", 4_000_000),
            item(
                "tifrs-fr1:NetCashFlowsFromUsedInOperatingActivities",
                "營業活動之淨現金流入（流出）",
                1_100_000,
            ),
            item(
                "tifrs-fr1:PaymentsToAcquirePropertyPlantAndEquipment",
                "取得不動產、廠房及設備",
                -600_000,
            ),
        ],
    )

    assert record.status == "available"
    assert record.period == "2025FY"
    assert record.revenue == 2_800_000
    assert record.total_assets == 6_000_000
    assert record.operating_cash_flow == 1_100_000
    assert record.capital_expenditure == -600_000
    assert "revenue" in record.concept_matches
    assert "year=114" in record.source_url


class FakeFetcher:
    def __init__(self):
        self.calls: list[tuple[str, int, int, str]] = []

    async def get_simplified_statement_async(
        self,
        *,
        stock_id: str,
        year: int,
        quarter: int,
        statement_type: str,
    ):
        self.calls.append((stock_id, year, quarter, statement_type))
        if year == 114:
            raise RuntimeError("annual filing not available")

        by_type = {
            "income_statement": [
                item("tifrs-fr1:Revenue", "營業收入", year * 1000),
                item("tifrs-fr1:ProfitLoss", "本期淨利", year * 100),
            ],
            "balance_sheet": [
                item("tifrs-fr1:Assets", "資產總額", year * 2000),
            ],
            "cash_flow": [
                item(
                    "tifrs-fr1:NetCashFlowsFromUsedInOperatingActivities",
                    "營業活動之淨現金流量",
                    year * 50,
                )
            ],
        }
        return SimpleNamespace(items=by_type[statement_type])


def test_fetch_history_keeps_error_period_but_collects_requested_available_years(tsmc):
    fetcher = FakeFetcher()
    client = MopsInlineXbrlClient(fetcher=fetcher)

    periods = asyncio.run(client.fetch_history(tsmc, years=3, end_roc_year=114))

    available = [period for period in periods if period.status == "available"]
    errors = [period for period in periods if period.status == "error"]
    assert len(available) == 3
    assert len(errors) == 1
    assert errors[0].period == "2025FY"
    assert {period.period for period in available} == {"2022FY", "2023FY", "2024FY"}
    assert any(call[3] == "cash_flow" for call in fetcher.calls)
