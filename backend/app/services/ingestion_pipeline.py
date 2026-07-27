from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.pipeline_models import CompanyRefreshResult, RefreshAllResult
from app.services.analysis_repository import AnalysisRepository, build_analysis_repository
from app.services.company_registry import get_company, list_companies
from app.services.financial_analysis_service import FinancialAnalysisService, UnsupportedCompanyError
from app.services.frontend_presenter import build_frontend_snapshot
from app.services.historical_analysis_service import HistoricalFinancialAnalysisService


TriggerKind = Literal["scheduler", "manual", "demo", "startup"]


class FinancialIngestionPipeline:
    def __init__(
        self,
        *,
        repository: AnalysisRepository | None = None,
        latest_service: FinancialAnalysisService | None = None,
        historical_service: HistoricalFinancialAnalysisService | None = None,
    ) -> None:
        self.repository = repository or build_analysis_repository()
        self.latest_service = latest_service or FinancialAnalysisService()
        self.historical_service = historical_service or HistoricalFinancialAnalysisService()

    async def refresh_company(
        self,
        ticker: str,
        *,
        years: int = 5,
        end_year: int | None = None,
        trigger: TriggerKind = "manual",
    ) -> CompanyRefreshResult:
        profile = get_company(ticker)
        if profile is None:
            raise UnsupportedCompanyError(
                "MVP 僅分析已登錄的半導體公司；請先將公司加入 semiconductor registry。"
            )

        run_id = uuid4().hex
        started_at = datetime.now(timezone.utc)
        try:
            latest_report = await self.latest_service.analyze(profile.ticker)
            historical_report = await self.historical_service.analyze(
                profile.ticker,
                years=years,
                end_roc_year=end_year - 1911 if end_year is not None else None,
            )
            snapshot = build_frontend_snapshot(
                run_id=run_id,
                latest_report=latest_report,
                historical_report=historical_report,
            )
            completed_at = datetime.now(timezone.utc)
            persistence = self.repository.save_pipeline_result(
                run_id=run_id,
                trigger=trigger,
                started_at=started_at,
                completed_at=completed_at,
                latest_report=latest_report,
                historical_report=historical_report,
                snapshot=snapshot,
            )
            return CompanyRefreshResult(
                run_id=run_id,
                ticker=profile.ticker,
                company_name=profile.name,
                subindustry=profile.subindustry,
                trigger=trigger,
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                latest_report_period=latest_report.report_period,
                history_available_years=historical_report.available_years,
                persistence=persistence,
                snapshot=snapshot,
            )
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            return CompanyRefreshResult(
                run_id=run_id,
                ticker=profile.ticker,
                company_name=profile.name,
                subindustry=profile.subindustry,
                trigger=trigger,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                error=str(exc),
            )

    async def refresh_all(
        self,
        *,
        years: int = 5,
        end_year: int | None = None,
        trigger: TriggerKind = "scheduler",
    ) -> RefreshAllResult:
        started_at = datetime.now(timezone.utc)
        results: list[CompanyRefreshResult] = []
        for company in list_companies():
            results.append(
                await self.refresh_company(
                    company.ticker,
                    years=years,
                    end_year=end_year,
                    trigger=trigger,
                )
            )
        completed_at = datetime.now(timezone.utc)
        completed = sum(result.status == "completed" for result in results)
        return RefreshAllResult(
            started_at=started_at,
            completed_at=completed_at,
            trigger=trigger,
            requested_companies=len(results),
            completed_companies=completed,
            failed_companies=len(results) - completed,
            results=results,
        )
