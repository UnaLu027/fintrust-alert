from __future__ import annotations

import os
import secrets
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.dependencies import get_analysis_repository, get_fact_repository
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
from app.pipeline_models import (
    AnalysisRunSummary,
    CompanyRefreshResult,
    FrontendAnalysisSnapshot,
    RefreshAllResult,
)
from app.services.analysis_repository import AnalysisRepository
from app.services.claim_parser import extract_claim
from app.services.company_registry import list_companies
from app.services.fact_repository import FinancialFactRepository
from app.services.financial_analysis_service import (
    FinancialAnalysisService,
    UnsupportedCompanyError,
)
from app.services.financial_rule_engine import FinancialRuleEngine
from app.services.historical_analysis_service import HistoricalFinancialAnalysisService
from app.services.ingestion_pipeline import FinancialIngestionPipeline
from app.services.mops_inline_xbrl import MopsInlineXbrlError
from app.services.twse_openapi import TwseOpenApiError
from app.services.verifier import verify_claim


router = APIRouter(prefix="/api/v1/financial", tags=["financial-evidence"])


def require_ingestion_token(
    x_ingestion_token: str | None = Header(default=None, alias="X-Ingestion-Token"),
) -> None:
    expected = os.getenv("INGESTION_API_TOKEN", "").strip()
    production = os.getenv("APP_ENV", "development").strip().lower() == "production"
    if not expected:
        if production:
            raise HTTPException(
                status_code=503,
                detail="Production ingestion endpoint requires INGESTION_API_TOKEN.",
            )
        return
    if x_ingestion_token is None or not secrets.compare_digest(x_ingestion_token, expected):
        raise HTTPException(status_code=401, detail="Invalid ingestion token.")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        module="semiconductor_financial_rule_engine_mvp",
        method="scheduled_ingestion_plus_persistent_analysis_snapshots",
        twse_openapi_ready=True,
        rule_engine_ready=True,
        historical_xbrl_ready=True,
    )


@router.get("/companies", response_model=CompanyListResponse)
def companies() -> CompanyListResponse:
    return CompanyListResponse(
        companies=list_companies(),
        note=(
            "此為可擴充的半導體公司 seed registry；系統依晶圓代工、IC 設計、"
            "封裝測試載入共通規則與子產業複合規則。"
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


@router.post(
    "/admin/companies/{ticker}/refresh",
    response_model=CompanyRefreshResult,
    dependencies=[Depends(require_ingestion_token)],
)
async def refresh_company_pipeline(
    ticker: str,
    years: int = Query(default=5, ge=3, le=5),
    end_year: int | None = Query(default=None, ge=2019, le=datetime.now().year),
    trigger: Literal["scheduler", "manual", "demo", "startup"] = Query(default="manual"),
    source_mode: Literal["official", "demo_fixture"] = Query(
        default="official",
        description=(
            "official 會連線 TWSE／MOPS；demo_fixture 僅在外部來源無法連線時驗證流程，"
            "回傳內容會明確標示為合成資料。"
        ),
    ),
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> CompanyRefreshResult:
    result = await FinancialIngestionPipeline(repository=repository).refresh_company(
        ticker,
        years=years,
        end_year=end_year,
        trigger=trigger,
        source_mode=source_mode,
    )
    if result.status == "failed":
        raise HTTPException(status_code=502, detail=result.error or "Financial refresh failed.")
    return result


@router.post(
    "/admin/refresh-all",
    response_model=RefreshAllResult,
    dependencies=[Depends(require_ingestion_token)],
)
async def refresh_all_company_pipelines(
    years: int = Query(default=5, ge=3, le=5),
    end_year: int | None = Query(default=None, ge=2019, le=datetime.now().year),
    trigger: Literal["scheduler", "manual", "demo", "startup"] = Query(default="scheduler"),
    source_mode: Literal["official", "demo_fixture"] = Query(default="official"),
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> RefreshAllResult:
    return await FinancialIngestionPipeline(repository=repository).refresh_all(
        years=years,
        end_year=end_year,
        trigger=trigger,
        source_mode=source_mode,
    )


@router.get(
    "/companies/{ticker}/analysis/latest",
    response_model=FrontendAnalysisSnapshot,
)
def latest_persisted_analysis(
    ticker: str,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> FrontendAnalysisSnapshot:
    snapshot = repository.get_latest_snapshot(ticker)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="尚無已完成的分析快照；請等待排程或由管理端執行 refresh。",
        )
    return snapshot


@router.get("/companies/{ticker}/metrics")
def persisted_metrics(
    ticker: str,
    limit: int = Query(default=200, ge=1, le=1000),
    run_id: str | None = Query(default=None, description="只回傳指定 analysis run 的指標。"),
    latest_only: bool = Query(
        default=False,
        description="自動使用最新 snapshot 的 run_id，避免混入舊分析紀錄。",
    ),
    repository: AnalysisRepository = Depends(get_analysis_repository),
):
    selected_run_id = run_id
    if latest_only:
        snapshot = repository.get_latest_snapshot(ticker)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="尚無已完成的分析快照。")
        selected_run_id = snapshot.analysis_run_id
    return {
        "ticker": ticker,
        "run_id": selected_run_id,
        "metrics": repository.list_metrics(ticker, limit, selected_run_id),
    }


@router.get(
    "/companies/{ticker}/analysis-runs",
    response_model=list[AnalysisRunSummary],
)
def analysis_runs(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100),
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> list[AnalysisRunSummary]:
    return repository.list_runs(ticker, limit)


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
    repository: AnalysisRepository = Depends(get_analysis_repository),
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
            "Compatibility endpoint only. Normal operation uses the scheduled ingestion pipeline, "
            "which fetches official data, persists facts, calculates metrics, executes rules and "
            "updates the frontend snapshot automatically."
        ),
    }
