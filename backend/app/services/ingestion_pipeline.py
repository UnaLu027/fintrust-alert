from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.financial_analysis_models import FinancialStatementAnalysisReport
from app.historical_analysis_models import HistoricalFinancialAnalysisReport
from app.pipeline_models import CompanyRefreshResult, RefreshAllResult
from app.services.analysis_repository import AnalysisRepository, build_analysis_repository
from app.services.company_registry import get_company, list_companies
from app.services.demo_fixture_sources import (
    DEMO_SOURCE_URL,
    DemoMopsInlineXbrlClient,
    DemoTwseOpenApiClient,
)
from app.services.financial_analysis_service import FinancialAnalysisService, UnsupportedCompanyError
from app.services.frontend_presenter import build_frontend_snapshot
from app.services.historical_analysis_service import HistoricalFinancialAnalysisService


logger = logging.getLogger("fintrust.ingestion")
TriggerKind = Literal["scheduler", "manual", "demo", "startup"]
SourceMode = Literal["official", "demo_fixture"]


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

    def _services_for_mode(
        self,
        source_mode: SourceMode,
    ) -> tuple[FinancialAnalysisService, HistoricalFinancialAnalysisService]:
        if source_mode == "official":
            return self.latest_service, self.historical_service
        if source_mode == "demo_fixture":
            return (
                FinancialAnalysisService(twse_client=DemoTwseOpenApiClient()),
                HistoricalFinancialAnalysisService(mops_client=DemoMopsInlineXbrlClient()),
            )
        raise ValueError(f"Unsupported source mode: {source_mode}")

    @staticmethod
    def _label_demo_reports(
        latest_report: FinancialStatementAnalysisReport,
        historical_report: HistoricalFinancialAnalysisReport,
    ) -> None:
        warning = (
            "DEMO FIXTURE：本次使用合成資料驗證正規化、指標、規則、資料庫與前端快照流程；"
            "不得解讀為公司真實財報或官方最新數值。"
        )
        latest_report.summary = f"[DEMO FIXTURE] {latest_report.summary}"
        latest_report.limitations = [warning, *latest_report.limitations]
        latest_report.statement.data_quality_warnings = [
            warning,
            *latest_report.statement.data_quality_warnings,
        ]
        for source in latest_report.statement.source_coverage:
            source.source_name = f"DEMO FIXTURE／{source.source_name}欄位結構"
            source.source_url = DEMO_SOURCE_URL

        historical_report.source_method = "DEMO FIXTURE synthetic annual Q4 records"
        historical_report.summary = f"[DEMO FIXTURE] {historical_report.summary}"
        historical_report.limitations = [warning, *historical_report.limitations]

    async def refresh_company(
        self,
        ticker: str,
        *,
        years: int = 5,
        end_year: int | None = None,
        trigger: TriggerKind = "manual",
        source_mode: SourceMode = "official",
    ) -> CompanyRefreshResult:
        profile = get_company(ticker)
        if profile is None:
            raise UnsupportedCompanyError(
                "MVP 僅分析已登錄的半導體公司；請先將公司加入 semiconductor registry。"
            )

        latest_service, historical_service = self._services_for_mode(source_mode)
        run_id = uuid4().hex
        started_at = datetime.now(timezone.utc)
        logger.info(
            "pipeline_started run_id=%s ticker=%s subindustry=%s years=%s trigger=%s source_mode=%s",
            run_id,
            profile.ticker,
            profile.subindustry,
            years,
            trigger,
            source_mode,
        )
        try:
            logger.info(
                "stage=twse_fetch run_id=%s ticker=%s source_mode=%s",
                run_id,
                profile.ticker,
                source_mode,
            )
            latest_report = await latest_service.analyze(profile.ticker)
            logger.info(
                "stage=twse_complete run_id=%s ticker=%s report_period=%s metrics=%s rules=%s",
                run_id,
                profile.ticker,
                latest_report.report_period,
                len(latest_report.metrics),
                len(latest_report.rule_results),
            )

            logger.info(
                "stage=mops_fetch run_id=%s ticker=%s years=%s source_mode=%s",
                run_id,
                profile.ticker,
                years,
                source_mode,
            )
            historical_report = await historical_service.analyze(
                profile.ticker,
                years=years,
                end_roc_year=end_year - 1911 if end_year is not None else None,
            )
            logger.info(
                "stage=mops_complete run_id=%s ticker=%s available_years=%s metrics=%s rules=%s rule_version=%s",
                run_id,
                profile.ticker,
                historical_report.available_years,
                len(historical_report.trend_metrics),
                len(historical_report.rule_results),
                historical_report.rule_version,
            )

            if source_mode == "demo_fixture":
                self._label_demo_reports(latest_report, historical_report)

            logger.info("stage=frontend_transform run_id=%s ticker=%s", run_id, profile.ticker)
            snapshot = build_frontend_snapshot(
                run_id=run_id,
                latest_report=latest_report,
                historical_report=historical_report,
            )
            completed_at = datetime.now(timezone.utc)

            logger.info(
                "stage=persist run_id=%s ticker=%s backend=%s",
                run_id,
                profile.ticker,
                self.repository.backend_name,
            )
            persistence = self.repository.save_pipeline_result(
                run_id=run_id,
                trigger=trigger,
                started_at=started_at,
                completed_at=completed_at,
                latest_report=latest_report,
                historical_report=historical_report,
                snapshot=snapshot,
            )
            logger.info(
                "pipeline_completed run_id=%s ticker=%s source_mode=%s filings=%s facts=%s metrics=%s rules=%s snapshots=%s",
                run_id,
                profile.ticker,
                source_mode,
                persistence.filings,
                persistence.facts,
                persistence.metrics,
                persistence.rule_results,
                persistence.snapshots,
            )
            return CompanyRefreshResult(
                run_id=run_id,
                ticker=profile.ticker,
                company_name=profile.name,
                subindustry=profile.subindustry,
                trigger=trigger,
                source_mode=source_mode,
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
            logger.exception(
                "pipeline_failed run_id=%s ticker=%s source_mode=%s error=%s",
                run_id,
                profile.ticker,
                source_mode,
                exc,
            )
            return CompanyRefreshResult(
                run_id=run_id,
                ticker=profile.ticker,
                company_name=profile.name,
                subindustry=profile.subindustry,
                trigger=trigger,
                source_mode=source_mode,
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
        source_mode: SourceMode = "official",
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
                    source_mode=source_mode,
                )
            )
        completed_at = datetime.now(timezone.utc)
        completed = sum(result.status == "completed" for result in results)
        return RefreshAllResult(
            started_at=started_at,
            completed_at=completed_at,
            trigger=trigger,
            source_mode=source_mode,
            requested_companies=len(results),
            completed_companies=completed,
            failed_companies=len(results) - completed,
            results=results,
        )
