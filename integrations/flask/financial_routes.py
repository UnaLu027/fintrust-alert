"""Flask proxy routes for the shared Financial Risk Alert System.

Copy this file into the shared Flask project and register the blueprint in
app.py. The routes keep the browser connected to the shared Flask host while the
Flask server calls the FinTrust FastAPI service behind the scenes.
"""

from __future__ import annotations

from typing import Any

from fintrust_client import FinTrustClient, FinTrustClientError


def create_financial_blueprint(client: FinTrustClient | None = None):
    """Create a Flask Blueprint with FinTrust proxy endpoints.

    Flask is imported inside the factory so this integration package can still be
    linted or unit-tested without installing Flask in the FastAPI repository.
    """

    from flask import Blueprint, jsonify, request

    blueprint = Blueprint("financial_proxy", __name__)

    def get_client() -> FinTrustClient:
        return client or FinTrustClient()

    def to_response(payload: Any, status_code: int = 200):
        return jsonify(payload), status_code

    def handle_error(error: FinTrustClientError):
        status = error.status_code or 502
        if status < 400:
            status = 502
        return to_response(
            {
                "success": False,
                "error": str(error),
                "detail": error.detail,
                "status_code": status,
            },
            status,
        )

    @blueprint.get("/api/financial/companies/<ticker>/analysis/latest")
    def latest_analysis(ticker: str):
        try:
            return to_response({"success": True, "data": get_client().latest_analysis(ticker)})
        except FinTrustClientError as exc:
            return handle_error(exc)

    @blueprint.get("/api/financial/companies/<ticker>/metrics")
    def metrics(ticker: str):
        try:
            latest_only = request.args.get("latest_only", "true").lower() != "false"
            limit = int(request.args.get("limit", "1000"))
            return to_response(
                {
                    "success": True,
                    "data": get_client().metrics(ticker, latest_only=latest_only, limit=limit),
                }
            )
        except (ValueError, FinTrustClientError) as exc:
            if isinstance(exc, FinTrustClientError):
                return handle_error(exc)
            return to_response({"success": False, "error": "Invalid limit parameter."}, 400)

    @blueprint.get("/api/financial/companies/<ticker>/analysis-runs")
    def analysis_runs(ticker: str):
        try:
            return to_response({"success": True, "data": get_client().analysis_runs(ticker)})
        except FinTrustClientError as exc:
            return handle_error(exc)

    @blueprint.post("/api/financial/admin/companies/<ticker>/refresh")
    def refresh_company(ticker: str):
        try:
            payload = request.get_json(silent=True) or {}
            return to_response(
                {
                    "success": True,
                    "data": get_client().refresh_company(
                        ticker,
                        years=int(payload.get("years", request.args.get("years", 3))),
                        end_year=payload.get("end_year") or request.args.get("end_year"),
                        trigger=payload.get("trigger", request.args.get("trigger", "manual")),
                        source_mode=payload.get("source_mode", request.args.get("source_mode", "official")),
                    ),
                }
            )
        except (ValueError, FinTrustClientError) as exc:
            if isinstance(exc, FinTrustClientError):
                return handle_error(exc)
            return to_response({"success": False, "error": "Invalid refresh parameters."}, 400)

    return blueprint
