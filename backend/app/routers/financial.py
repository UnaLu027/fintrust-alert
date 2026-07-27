from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_fact_repository
from app.financial_analysis_models import (
    FinancialStatementAnalysisReport,
    RuleCatalogResponse,
)
from app.historical_analysis_models import HistoricalFinancialAnalysisReport
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
from app.services.financial_analysis_service import (
    FinancialAnalysisService,
    UnsupportedCompanyError,
)
from app.services.financial_rule_engine import FinancialRuleEngine
from app.services.historical_analysis_service import HistoricalFinancialAnalysisService
from app.services.mops_inline_xbrl import MopsInlineXbrlError
from app.services.twse_openapi import TwseOpenApiError
from app.services.verifier import verify_claim

router = APIRouter(prefix="/api/v1/financial", tags=["financial-evidence"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        module="semiconductor_financial_rule_engine_mvp",
        method="live_twse_snapshot_plus_mops_ixbrl_history_and_versioned_rules",
        twse_openapi_ready=True,
        rule_engine_ready=True,
        historical_xbrl_ready=True,
    )


@router.get("/companies", response_model=CompanyListResponse)
def companies() -> CompanyListResponse:
    return CompanyListResponse(
        companies=list_companies(),
        note=(
            "此為可擴充的半導體公司 seed registry；系統不限定晶圓代工，"
            "同業基準功能只會比較相同子產業。"
        ),
    )


@router.get("/rules", response_model=RuleCatalogResponse)
def rules() -> RuleCatalogResponse:
    return FinancialRuleEngine().catalog()


@router.get(
    "/statements/{ticker}/analyze",
    response_model=FinancialStatementAnalysisReport,
)
async def analyze_financial_statement(ticker: str) -> FinancialStatementAnalysisReport:
    try:
        return await FinancialAnalysisService().analyze(ticker)
    except UnsupportedCompanyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TwseOpenApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"無法取得臺灣證券交易所財報資料：{exc}",
        ) from exc


@router.get(
    "/statements/{ticker}/history",
    response_model=HistoricalFinancialAnalysisReport,
)
async def analyze_historical_financial_statements(
    ticker: str,
    years: int = Query(default=5, ge=3, le=5),
    end_year: int | None = Query(
        default=None,
        ge=2019,
        le=datetime.now().year,
        description="最後一個財報年度（西元年）；未提供時使用最近已完成年度。",
    ),
) -> HistoricalFinancialAnalysisReport:
    end_roc_year = end_year - 1911 if end_year is not None else None
    try:
        return await HistoricalFinancialAnalysisService().analyze(
            ticker,
            years=years,
            end_roc_year=end_roc_year,
        )
    except UnsupportedCompanyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MopsInlineXbrlError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"無法取得 MOPS Inline XBRL 歷史財報：{exc}",
        ) from exc


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
