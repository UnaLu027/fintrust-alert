"""Small client for connecting the shared Flask app to the FinTrust FastAPI service.

This file is intentionally dependency-light so it can be copied into the shared
Flask project without bringing the whole FastAPI backend with it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class FinTrustClientError(RuntimeError):
    """Raised when the Flask integration cannot reach or parse FinTrust API."""

    def __init__(self, message: str, *, status_code: int | None = None, detail: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


Opener = Callable[[Request, float], Any]


@dataclass(slots=True)
class FinTrustClient:
    """HTTP client used by Flask proxy routes.

    The browser should call Flask routes, not the FastAPI service directly.
    This keeps API URLs, ingestion tokens and future OpenAI settings on the
    server side.
    """

    base_url: str | None = None
    ingestion_token: str | None = None
    timeout_seconds: float = 20.0
    opener: Opener | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.base_url = (self.base_url or os.getenv("FINTRUST_API_BASE_URL", "")).strip().rstrip("/")
        self.ingestion_token = (self.ingestion_token or os.getenv("FINTRUST_INGESTION_TOKEN", "")).strip()
        if not self.base_url:
            raise FinTrustClientError("FINTRUST_API_BASE_URL is not configured.")

    def _url(self, path: str, params: dict[str, Any] | None = None) -> str:
        clean_path = path if path.startswith("/") else f"/{path}"
        query = urlencode({key: value for key, value in (params or {}).items() if value is not None})
        return f"{self.base_url}{clean_path}" + (f"?{query}" if query else "")

    def _open(self, request: Request) -> Any:
        if self.opener is not None:
            return self.opener(request, self.timeout_seconds)
        return urlopen(request, timeout=self.timeout_seconds)  # noqa: S310 - URL is configured server-side.

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        include_ingestion_token: bool = False,
    ) -> Any:
        body = None
        headers = {"Accept": "application/json"}
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if include_ingestion_token and self.ingestion_token:
            headers["X-Ingestion-Token"] = self.ingestion_token

        request = Request(
            self._url(path, params),
            data=body,
            headers=headers,
            method=method.upper(),
        )
        try:
            with self._open(request) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return None
                return json.loads(raw)
        except HTTPError as exc:
            detail = self._safe_error_detail(exc)
            raise FinTrustClientError(
                "FinTrust API returned an error.",
                status_code=exc.code,
                detail=detail,
            ) from exc
        except URLError as exc:
            raise FinTrustClientError(
                "FinTrust API is unreachable.",
                status_code=502,
                detail=str(exc.reason),
            ) from exc
        except (TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise FinTrustClientError(
                "FinTrust API response could not be processed.",
                status_code=502,
                detail=str(exc),
            ) from exc

    @staticmethod
    def _safe_error_detail(error: HTTPError) -> Any:
        try:
            payload = error.read().decode("utf-8")
            return json.loads(payload) if payload else None
        except Exception:  # pragma: no cover - best effort error detail only
            return None

    def latest_analysis(self, ticker: str) -> Any:
        return self.request("GET", f"/api/v1/financial/companies/{ticker}/analysis/latest")

    def metrics(self, ticker: str, *, latest_only: bool = True, limit: int = 1000) -> Any:
        return self.request(
            "GET",
            f"/api/v1/financial/companies/{ticker}/metrics",
            params={"latest_only": str(latest_only).lower(), "limit": limit},
        )

    def analysis_runs(self, ticker: str) -> Any:
        return self.request("GET", f"/api/v1/financial/companies/{ticker}/analysis-runs")

    def refresh_company(
        self,
        ticker: str,
        *,
        years: int = 3,
        end_year: int | None = None,
        trigger: str = "manual",
        source_mode: str = "official",
    ) -> Any:
        return self.request(
            "POST",
            f"/api/v1/financial/admin/companies/{ticker}/refresh",
            params={
                "years": years,
                "end_year": end_year,
                "trigger": trigger,
                "source_mode": source_mode,
            },
            include_ingestion_token=True,
        )
