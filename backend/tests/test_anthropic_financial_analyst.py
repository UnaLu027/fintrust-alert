import json
from types import SimpleNamespace

import pytest

from app.ai_analysis_models import AnalysisDimension, DimensionAssessment, DimensionSignal
from app.services.anthropic_financial_analyst import AnthropicFinancialAnalyst
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


class FakeMessages:
    def __init__(self, *, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.last_kwargs = None

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, messages: FakeMessages):
        self.messages = messages


def _response(text: str, *, stop_reason: str = "end_turn"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
    )


@pytest.mark.asyncio
async def test_anthropic_not_configured_returns_safe_trace():
    analyst = AnthropicFinancialAnalyst(api_key="", model="claude-sonnet-5")
    narrative, trace = await analyst.analyze(
        company_name="聯發科",
        ticker="2454",
        subindustry="IC 設計",
        dimensions=_dimensions(),
        rules=[],
    )
    assert narrative is None
    assert trace.status == "not_configured"
    assert trace.provider == "anthropic"
    assert trace.provider_configured is False


def test_anthropic_blank_model_env_falls_back_to_sonnet_5(monkeypatch):
    monkeypatch.setenv("FINANCIAL_LLM_MODEL", "")
    analyst = AnthropicFinancialAnalyst(api_key="demo-key")
    assert analyst.model == "claude-sonnet-5"
    assert analyst.configured is True


@pytest.mark.asyncio
async def test_anthropic_success_uses_current_structured_output_shape():
    messages = FakeMessages(response=_response(_narrative_json()))
    analyst = AnthropicFinancialAnalyst(
        api_key="demo-key",
        model="claude-sonnet-5",
        client=FakeClient(messages),
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
    assert trace.provider == "anthropic"
    assert trace.model == "claude-sonnet-5"
    output_format = messages.last_kwargs["output_config"]["format"]
    assert output_format["type"] == "json_schema"
    assert "schema" in output_format
    assert "json_schema" not in output_format


@pytest.mark.asyncio
async def test_anthropic_api_failure_is_fail_safe():
    messages = FakeMessages(error=RuntimeError("simulated Anthropic outage"))
    analyst = AnthropicFinancialAnalyst(
        api_key="demo-key",
        model="claude-sonnet-5",
        client=FakeClient(messages),
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
    assert trace.provider == "anthropic"
    assert "simulated Anthropic outage" in (trace.error or "")


def test_anthropic_health_matches_provider_contract():
    analyst = AnthropicFinancialAnalyst(api_key="demo-key", model="claude-sonnet-5")
    health = analyst.health()
    assert health["provider"] == "anthropic"
    assert health["configured"] is True
    assert health["provider_configured"] is True
    assert health["endpoint_configured"] is False
    assert health["structured_output"] is True


def test_factory_selects_anthropic_and_unknown_provider_does_not_silently_fallback(monkeypatch):
    monkeypatch.setenv("FINANCIAL_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "demo-key")
    monkeypatch.setenv("FINANCIAL_LLM_MODEL", "claude-sonnet-5")
    analyst = create_financial_llm_provider()
    assert analyst.provider_name == "anthropic"

    monkeypatch.setenv("FINANCIAL_LLM_PROVIDER", "anthropic_typo")
    invalid = create_financial_llm_provider()
    assert invalid.provider_name == "anthropic_typo"
    assert invalid.configured is False
    assert "Unsupported FINANCIAL_LLM_PROVIDER" in invalid.health()["error"]
