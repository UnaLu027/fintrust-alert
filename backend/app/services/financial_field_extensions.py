from __future__ import annotations

from app.services.mops_inline_xbrl import FIELD_ALIASES, INSTANT_FIELDS


EXTENDED_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "cost_of_goods_sold": (
        "營業成本",
        "營業成本合計",
        "OperatingCosts",
        "CostOfGoodsSold",
        "CostOfRevenue",
    ),
    "accounts_receivable": (
        "應收帳款淨額",
        "應收帳款",
        "應收票據及應收帳款淨額",
        "AccountsReceivableNet",
        "AccountsReceivable",
        "TradeReceivables",
        "NotesAndAccountsReceivableNet",
    ),
}


def register_analysis_field_aliases() -> None:
    """Extend the shared MOPS taxonomy map without changing the stable parser core."""
    for field, aliases in EXTENDED_FIELD_ALIASES.items():
        if field not in FIELD_ALIASES:
            FIELD_ALIASES[field] = aliases
    INSTANT_FIELDS.add("accounts_receivable")
