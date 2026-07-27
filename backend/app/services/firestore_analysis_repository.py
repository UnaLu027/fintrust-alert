from __future__ import annotations

from datetime import datetime
from typing import Any

from app.financial_analysis_models import FinancialStatementAnalysisReport
from app.historical_analysis_models import HistoricalFinancialAnalysisReport
from app.pipeline_models import AnalysisRunSummary, FrontendAnalysisSnapshot, PersistenceCounts
from app.services.analysis_repository import (
    document_id,
    historical_fact_rows,
    latest_fact_rows,
    metric_rows,
    rule_rows,
)


class FirestoreAnalysisRepository:
    backend_name = "firestore"

    def __init__(self, project_id: str | None = None) -> None:
        from google.cloud import firestore

        self.client = firestore.Client(project=project_id or None)

    def save_pipeline_result(
        self,
        *,
        run_id: str,
        trigger: str,
        started_at: datetime,
        completed_at: datetime,
        latest_report: FinancialStatementAnalysisReport,
        historical_report: HistoricalFinancialAnalysisReport,
        snapshot: FrontendAnalysisSnapshot,
    ) -> PersistenceCounts:
        facts = latest_fact_rows(latest_report) + historical_fact_rows(historical_report)
        metrics = metric_rows(run_id, latest_report, historical_report)
        rules = rule_rows(run_id, latest_report, historical_report)
        batch = self.client.batch()

        batch.set(
            self.client.collection("analysis_runs").document(run_id),
            {
                "run_id": run_id,
                "ticker": historical_report.ticker,
                "company_name": historical_report.company_name,
                "subindustry": historical_report.subindustry,
                "analysis_type": "combined",
                "trigger": trigger,
                "status": "completed",
                "started_at": started_at,
                "completed_at": completed_at,
                "rule_version": historical_report.rule_version,
                "overall_severity": snapshot.overall_severity.value,
                "summary": snapshot.summary,
                "error_message": None,
            },
        )

        for period in historical_report.periods:
            batch.set(
                self.client.collection("financial_filings").document(
                    document_id(historical_report.ticker, period.period)
                ),
                {
                    "ticker": historical_report.ticker,
                    "period": period.period,
                    "company_name": historical_report.company_name,
                    "subindustry": historical_report.subindustry,
                    "fiscal_year": period.fiscal_year,
                    "quarter": period.quarter,
                    "source_name": period.source_name,
                    "source_url": period.source_url,
                    "status": period.status,
                    "concept_matches": period.concept_matches,
                    "warnings": period.warnings,
                    "retrieved_at": completed_at,
                },
                merge=True,
            )

        for fact in facts:
            batch.set(
                self.client.collection("normalized_financial_facts").document(
                    document_id(
                        fact["ticker"],
                        fact["analysis_type"],
                        fact["period"],
                        fact["metric_code"],
                    )
                ),
                {**fact, "retrieved_at": completed_at},
                merge=True,
            )

        for metric in metrics:
            batch.set(
                self.client.collection("calculated_metrics").document(
                    document_id(
                        run_id,
                        metric["analysis_type"],
                        metric["period"],
                        metric["metric_code"],
                    )
                ),
                {**metric, "created_at": completed_at},
            )

        for rule in rules:
            batch.set(
                self.client.collection("rule_results").document(
                    document_id(run_id, rule["analysis_type"], rule["rule_id"])
                ),
                {**rule, "created_at": completed_at},
            )

        batch.set(
            self.client.collection("latest_analysis_snapshots").document(snapshot.ticker),
            {**snapshot.model_dump(mode="python"), "updated_at": completed_at},
        )
        batch.commit()

        return PersistenceCounts(
            filings=len(historical_report.periods),
            facts=len(facts),
            metrics=len(metrics),
            rule_results=len(rules),
            snapshots=1,
        )

    def get_latest_snapshot(self, ticker: str) -> FrontendAnalysisSnapshot | None:
        document = self.client.collection("latest_analysis_snapshots").document(ticker).get()
        if not document.exists:
            return None
        payload = document.to_dict() or {}
        payload.pop("updated_at", None)
        return FrontendAnalysisSnapshot.model_validate(payload)

    def list_metrics(self, ticker: str, limit: int = 200) -> list[dict[str, Any]]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        documents = self.client.collection("calculated_metrics").where(
            filter=FieldFilter("ticker", "==", ticker)
        ).stream()
        rows = [document.to_dict() or {} for document in documents]
        rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
        return rows[:limit]

    def list_runs(self, ticker: str, limit: int = 20) -> list[AnalysisRunSummary]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        documents = self.client.collection("analysis_runs").where(
            filter=FieldFilter("ticker", "==", ticker)
        ).stream()
        rows = [document.to_dict() or {} for document in documents]
        rows.sort(key=lambda row: str(row.get("started_at") or ""), reverse=True)
        return [AnalysisRunSummary.model_validate(row) for row in rows[:limit]]
