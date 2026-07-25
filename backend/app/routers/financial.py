from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_fact_repository
from app.models import (
    ClaimExtractionRequest,
    ClaimVerificationRequest,
    ClaimVerificationResult,
    CompanyListResponse,
    FactIngestRequest,
    HealthResponse,
)
from app.services.claim_parser import extract_claim
from app.services.company_registry import list_companies
from app.services.fact_repository import FinancialFactRepository
from app.services.verifier import verify_claim

router = APIRouter(prefix="/api/v1/financial", tags=["financial-evidence"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        module="semiconductor_financial_evidence_mvp",
        method="claim_extraction_and_deterministic_recalculation",
        historical_xbrl_ready=False,
    )


@router.get("/companies", response_model=CompanyListResponse)
def companies() -> CompanyListResponse:
    return CompanyListResponse(
        companies=list_companies(),
        note=(
            "此為可擴充的半導體公司 seed registry；系統不限定晶圓代工，"
            "但未來同業比較只允許相同子產業。"
        ),
    )


@router.post("/claims/extract")
def extract(payload: ClaimExtractionRequest):
    return extract_claim(
        payload.text,
        ticker_hint=payload.ticker,
        period_hint=payload.period,
        comparison_period_hint=payload.comparison_period,
    )


@router.post("/claims/verify", response_model=ClaimVerificationResult)
def verify(
    payload: ClaimVerificationRequest,
    repository: FinancialFactRepository = Depends(get_fact_repository),
) -> ClaimVerificationResult:
    claim = extract_claim(
        payload.text,
        ticker_hint=payload.ticker,
        period_hint=payload.period,
        comparison_period_hint=payload.comparison_period,
    )
    return verify_claim(claim, repository, payload.tolerance_percentage_points)


@router.post("/facts/ingest")
def ingest(
    payload: FactIngestRequest,
    repository: FinancialFactRepository = Depends(get_fact_repository),
):
    inserted = repository.upsert_many(payload.facts)
    return {
        "inserted": inserted,
        "warning": (
            "MVP endpoint accepts normalized facts only. The MOPS Inline XBRL "
            "downloader/parser must preserve source URL, taxonomy concept, period, unit and scope."
        ),
    }
