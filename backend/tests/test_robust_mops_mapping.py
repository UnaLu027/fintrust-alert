from types import SimpleNamespace

import pytest

from app.services.company_registry import get_company
from app.services.robust_mops_inline_xbrl import robust_normalize_mops_annual_package


def context(context_id: str, *, start: str | None = None, end: str | None = None, instant: str | None = None):
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
        unit="TWD",
    )


def test_robust_mapper_uses_twmops_cash_flow_concept_and_english_extension_label():
    company = get_company("2330")
    assert company is not None

    duration = "From20240101To20241231"
    instant = "AsOf20241231"
    package = SimpleNamespace(
        contexts={
            duration: context(duration, start="2024-01-01", end="2024-12-31"),
            instant: context(instant, instant="2024-12-31"),
        },
        facts=[
            fact("Revenue", 2_894_308_000, duration),
            fact("ProfitLoss", 1_173_268_000, duration),
            fact("Assets", 6_685_793_000, instant),
            fact("Liabilities", 2_365_318_000, instant),
            fact("CashFlowsFromUsedInOperatingActivities", 1_826_177_068, duration),
            fact("TSMCCustomPPECashPayments", -949_816_825, duration),
        ],
        labels={
            "Revenue": "營業收入",
            "ProfitLoss": "本期淨利",
            "Assets": "資產總額",
            "Liabilities": "負債總額",
        },
        labels_en={
            "CashFlowsFromUsedInOperatingActivities": "Cash flows from operating activities",
            "TSMCCustomPPECashPayments": "Payments to acquire property, plant and equipment",
        },
    )

    record = robust_normalize_mops_annual_package(company, 113, package)

    assert record.status == "available"
    assert record.operating_cash_flow == pytest.approx(1_826_177_068)
    assert record.capital_expenditure == pytest.approx(-949_816_825)
    assert record.concept_matches["operating_cash_flow"] == "CashFlowsFromUsedInOperatingActivities"
    assert record.concept_matches["capital_expenditure"] == "TSMCCustomPPECashPayments"
    assert "year=113" in record.source_url


def test_robust_mapper_does_not_use_balance_sheet_ppe_as_capex():
    company = get_company("2330")
    assert company is not None

    duration = "currentDuration"
    instant = "currentInstant"
    package = SimpleNamespace(
        contexts={
            duration: context(duration, start="2024-01-01", end="2024-12-31"),
            instant: context(instant, instant="2024-12-31"),
        },
        facts=[
            fact("Revenue", 1000, duration),
            fact("ProfitLoss", 400, duration),
            fact("Assets", 3000, instant),
            fact("Liabilities", 1000, instant),
            fact("PropertyPlantAndEquipment", 1500, instant),
        ],
        labels={"PropertyPlantAndEquipment": "不動產、廠房及設備"},
        labels_en={},
    )

    record = robust_normalize_mops_annual_package(company, 113, package)
    assert record.capital_expenditure is None
