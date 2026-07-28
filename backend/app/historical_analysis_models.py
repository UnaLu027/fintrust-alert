from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.financial_analysis_models import RuleSeverity


class HistoricalPeriodRecord(BaseModel):
    ticker: str
    company_name: str
    subindustry: str
    fiscal_year: int
    roc_year: int
    quarter: Literal[4] = 4
    period: str
    source_name: str = "公開資訊觀測站 MOPS Inline XBRL"
    source_url: str
    status: Literal["available", "missing", "error"]

    revenue: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    eps: float | None = None

    cash_and_cash_equivalents: float | None = None
    inventory: float | None = None
    current_assets: float | None = None
    total_assets: float | None = None
    current_liabilities: float | None = None
    total_liabilities: float | None = None
    equity: float | None = None

    operating_cash_flow: float | None = None
    investing_cash_flow: float | None = None
    capital_expenditure: float | None = None
    research_and_development_expense: float | None = None

    # Arelle/twmops returns the decoded XBRL monetary value in the fact unit.
    # For official filings used by this MVP that unit is TWD, not thousands of
    # TWD. Keeping the label aligned prevents a 1,000x presentation error while
    # leaving ratio calculations unchanged.
    currency_unit: str = "新台幣元"
    fields_found: list[str] = Field(default_factory=list)
    fields_missing: list[str] = Field(default_factory=list)
    concept_matches: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class HistoricalTrendMetric(BaseModel):
    code: str
    label: str
    category: str
    unit: str
    period_values: dict[str, float] = Field(default_factory=dict)
    latest_value: float | None = None
    previous_value: float | None = None
    change_percent: float | None = None
    change_percentage_points: float | None = None
    formula: str
    source_fields: list[str] = Field(default_factory=list)


class HistoricalRuleResult(BaseModel):
    rule_id: str
    name: str
    category: str
    severity: RuleSeverity
    triggered: bool
    explanation: str
    threshold_description: str
    evidence_periods: list[str] = Field(default_factory=list)
    evidence_metrics: list[str] = Field(default_factory=list)
    rule_scope: str = "semiconductor_common"
    logic_expression: str | None = None
    actual_values: dict[str, float | None] = Field(default_factory=dict)


class HistoricalFinancialAnalysisReport(BaseModel):
    ticker: str
    company_name: str
    industry: Literal["半導體"] = "半導體"
    subindustry: str
    requested_years: int
    available_years: int
    start_year: int | None = None
    end_year: int | None = None
    analyzed_at: datetime
    source_method: str = "MOPS Inline XBRL annual Q4 filings"
    rule_version: str
    threshold_basis: str
    overall_severity: RuleSeverity
    summary: str
    periods: list[HistoricalPeriodRecord]
    trend_metrics: list[HistoricalTrendMetric]
    rule_results: list[HistoricalRuleResult]
    limitations: list[str] = Field(default_factory=list)
