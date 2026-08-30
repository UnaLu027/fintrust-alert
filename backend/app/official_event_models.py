from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


OfficialEvidenceType = Literal["financial_snapshot", "investor_conference", "material_event"]
OfficialEvidenceSourceStatus = Literal[
    "available",
    "metadata_only",
    "needs_manual_review",
    "missing",
    "error",
]
MaterialEventCategory = Literal[
    "financial_outlook",
    "capacity_or_capex",
    "revenue_or_orders",
    "inventory_or_demand",
    "financing_or_debt",
    "ma_or_investment",
    "operation_disruption",
    "legal_or_penalty",
    "governance",
    "other",
]


class OfficialSourceLink(BaseModel):
    source_name: str
    source_url: str
    status: OfficialEvidenceSourceStatus = "metadata_only"
    retrieved_at: datetime | None = None
    limitation: str | None = None


class InvestorConferenceRecord(BaseModel):
    ticker: str
    company_name: str
    subindustry: str
    fiscal_year: int | None = None
    quarter: int | None = None
    conference_date: str | None = None
    title: str
    source_name: str = "公開資訊觀測站 法說會"
    source_url: str
    document_url: str | None = None
    video_url: str | None = None
    status: OfficialEvidenceSourceStatus = "metadata_only"
    extracted_topics: list[str] = Field(default_factory=list)
    related_metrics: list[str] = Field(default_factory=list)
    summary: str | None = None
    limitations: list[str] = Field(default_factory=list)


class MaterialEventRecord(BaseModel):
    ticker: str
    company_name: str
    subindustry: str
    event_date: str | None = None
    title: str
    category: MaterialEventCategory = "other"
    source_name: str = "公開資訊觀測站 重大訊息"
    source_url: str
    status: OfficialEvidenceSourceStatus = "metadata_only"
    raw_text: str | None = None
    related_metrics: list[str] = Field(default_factory=list)
    risk_related: bool = False
    summary: str | None = None
    limitations: list[str] = Field(default_factory=list)


class OfficialEvidenceSummary(BaseModel):
    ticker: str
    company_name: str
    subindustry: str
    generated_at: datetime
    evidence_layers: list[OfficialEvidenceType]
    financial_snapshot: dict | None = None
    investor_conferences: list[InvestorConferenceRecord] = Field(default_factory=list)
    material_events: list[MaterialEventRecord] = Field(default_factory=list)
    official_evidence_summary: str
    readiness: Literal[
        "financial_only",
        "financial_plus_event_metadata",
        "ready_for_frontend_integration",
        "needs_refresh",
    ]
    limitations: list[str] = Field(default_factory=list)
    sources: list[OfficialSourceLink] = Field(default_factory=list)
