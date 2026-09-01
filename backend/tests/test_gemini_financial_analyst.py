import json
from types import SimpleNamespace

import pytest

from app.ai_analysis_models import AnalysisDimension, DimensionAssessment, DimensionSignal
from app.services.gemini_financial_analyst import GeminiFinancialAnalyst
from app.services.llm_provider_protocol import create_financial_llm_provider


DIMENSION_KEYS = [
    "growth",
    "profitability",
    "rd_innovation",
    "operating_efficiency",
    "cash_flow",
    "financial_structure",
    "earnings_quality",
    "investment_efficiency",
]


def _dimensions() -> list[DimensionAssessment]:
    return [
        DimensionAssessment(
            dimension=AnalysisDimension.GROWTH,
            label="成長性",
            signal=DimensionSignal.NORMAL,
            coverage_ratio=1.0,
            evaluated_rules=3,
            total_rules=3,
            triggered_rule_ids=[],
            direct_metrics=["revenue_growth_yoy"],
            indirect_metrics=[],
            summary="測試資料。",
        )
    ]


def _narrative_json() -> str:
    return json.dumps(
        {
            "executive_summary": "整體訊號偏穩定，但仍應搭配資料限制解讀。",
            "dimension_insights": {key: f"{key} 測試說明" for key in DIMENSION_KEYS},
            "watch_items": ["持續觀察跨期變化"],
            "limitations": ["僅依提供的官方財報衍生 evidence"],
        },
        ensure_ascii=False,
    )


class FakeModels:
    def __init__(self, *, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.last_kwargs = None
        self.calls = []

    async def generate_content(self, **kwargs):
        self.last_kwargs = kwargs
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, models):
        self.models = models


class FakeAPIError(RuntimeError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


class PrimaryUnavailableModels:
    def __init__(self, *, primary_model: str, fallback_response):
        self.primary_model = primary_model
        self.fallback_response = fallback_response
        self.calls = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs["model"] == self.primary_model:
            raise FakeAPIError(503, "simulated high demand")
        return self.fallback_response


def _response(text: str):
    return SimpleNamespace(text=text, parsed=None)


@pytest.mark.asyncio
async def test_gemini_not_configured_returns_safe_trace():
    analyst = GeminiFinancialAnalyst(api_key="", model="gemini-3.6-flash")
    narrative, trace = await analyst.analyze(
        company_name="聯發科",
        ticker="2454",
        subindustry="IC 設計",
        dimensions=_dimensions(),
        rules=[],
    )
    assert narrative is None
    assert trace.status == "not_configured"
    assert trace.provider == "gemini"
    assert trace.provider_configured is False


def test_gemini_blank_model_env_falls_back_to_36_flash(monkeypatch):
    monkeypatch.setenv("FINANCIAL_LLM_MODEL", "")
    analyst = GeminiFinancialAnalyst(api_key="demo-key")
    assert analyst.model == "gemini-3.6-flash"
    assert analyst.configured is True


def test_gemini_default_fallback_model_is_flash_lite(monkeypatch):
    monkeypatch.delenv("FINANCIAL_LLM_FALLBACK_MODEL", raising=False)
    analyst = GeminiFinancialAnalyst(api_key="demo-key", model="gemini-3.6-flash")
    assert analyst.fallback_model == "gemini-3.5-flash-lite"


def test_gemini_api_key_whitespace_is_stripped():
    analyst = GeminiFinancialAnalyst(api_key="  demo-key  ", model="gemini-3.6-flash")
    assert analyst._api_key == "demo-key"
    assert analyst.configured is True


@pytest.mark.asyncio
async def test_gemini_success_uses_json_schema_structured_output_without_deprecated_temperature():
    models = FakeModels(response=_response(_narrative_json()))
    analyst = GeminiFinancialAnalyst(
        api_key="demo-key",
        model="gemini-3.6-flash",
        client=FakeClient(models),
    )
    narrative, trace = await analyst.analyze(
        company_name="聯發科",
        ticker="2454",
        subindustry="IC 設計",
        dimensions=_dimensions(),
        rules=[],
    )
    assert narrative is not None
    assert narrative.executive_summary
    assert trace.status == "completed"
    assert trace.provider == "gemini"
    assert trace.model == "gemini-3.6-flash"
    config = models.last_kwargs["config"]
    assert config["response_mime_type"] == "application/json"
    assert config["response_json_schema"]["type"] == "object"
    assert set(config["response_json_schema"]["properties"]["dimension_insights"]["required"]) == set(DIMENSION_KEYS)
    assert "temperature" not in config


@pytest.mark.asyncio
async def test_gemini_503_uses_flash_lite_fallback():
    models = PrimaryUnavailableModels(
        primary_model="gemini-3.6-flash",
        fallback_response=_response(_narrative_json()),
    )
    analyst = GeminiFinancialAnalyst(
        api_key="demo-key",
        model="gemini-3.6-flash",
        fallback_model="gemini-3.5-flash-lite",
        client=FakeClient(models),
    )
    narrative, trace = await analyst.analyze(
        company_name="聯發科",
        ticker="2454",
        subindustry="IC 設計",
        dimensions=_dimensions(),
        rules=[],
    )
    assert narrative is not None
    assert trace.status == "completed"
    assert trace.model == "gemini-3.5-flash-lite"
    assert [call["model"] for call in models.calls] == ["gemini-3.6-flash", "gemini-3.5-flash-lite"]


@pytest.mark.asyncio
async def test_gemini_non_retryable_error_does_not_switch_models():
    error = FakeAPIError(400, "simulated invalid request")
    models = FakeModels(error=error)
    analyst = GeminiFinancialAnalyst(
        api_key="demo-key",
        model="gemini-3.6-flash",
        fallback_model="gemini-3.5-flash-lite",
        client=FakeClient(models),
    )
    narrative, trace = await analyst.analyze(
        company_name="聯發科",
        ticker="2454",
        subindustry="IC 設計",
        dimensions=_dimensions(),
        rules=[],
    )
    assert narrative is None
    assert trace.status == "failed"
    assert trace.model == "gemini-3.6-flash"
    assert len(models.calls) == 1


@pytest.mark.asyncio
async def test_gemini_api_failure_is_fail_safe():
    models = FakeModels(error=RuntimeError("simulated Gemini outage"))
    analyst = GeminiFinancialAnalyst(
        api_key="demo-key",
        model="gemini-3.6-flash",
        client=FakeClient(models),
    )
    narrative, trace = await analyst.analyze(
        company_name="聯發科",
        ticker="2454",
        subindustry="IC 設計",
        dimensions=_dimensions(),
        rules=[],
    )
    assert narrative is None
    assert trace.status == "failed"
    assert trace.provider == "gemini"
    assert "simulated Gemini outage" in (trace.error or "")


def test_gemini_health_matches_provider_contract():
    analyst = GeminiFinancialAnalyst(api_key="demo-key", model="gemini-3.6-flash")
    health = analyst.health()
    assert health["provider"] == "gemini"
    assert health["configured"] is True
    assert health["provider_configured"] is True
    assert health["endpoint_configured"] is False
    assert health["structured_output"] is True
    assert health["fallback_model"] == "gemini-3.5-flash-lite"


def test_factory_selects_gemini(monkeypatch):
    monkeypatch.setenv("FINANCIAL_LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "demo-key")
    monkeypatch.setenv("FINANCIAL_LLM_MODEL", "gemini-3.6-flash")
    analyst = create_financial_llm_provider()
    assert analyst.provider_name == "gemini"
    assert analyst.configured is True
