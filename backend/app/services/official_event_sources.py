from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlencode

from app.official_event_models import (
    InvestorConferenceRecord,
    MaterialEventCategory,
    MaterialEventRecord,
)
from app.services.company_registry import get_company
from app.services.financial_analysis_service import UnsupportedCompanyError


MOPS_BASE = "https://mops.twse.com.tw/mops/web"

CONFERENCE_TOPIC_METRICS: dict[str, list[str]] = {
    "晶圓代工": ["capex_intensity", "free_cash_flow", "gross_margin", "operating_margin", "debt_ratio"],
    "IC 設計": ["rd_intensity", "revenue_growth_yoy", "inventory_growth_yoy", "cash_conversion_ratio"],
    "封裝測試": ["inventory_growth_yoy", "operating_cash_flow", "cash_conversion_ratio", "debt_ratio", "current_ratio"],
}

MATERIAL_EVENT_KEYWORDS: tuple[tuple[MaterialEventCategory, tuple[str, ...], tuple[str, ...]], ...] = (
    ("capacity_or_capex", ("擴產", "產能", "資本支出", "建廠", "設備", "capex"), ("capex_intensity", "free_cash_flow", "debt_ratio")),
    ("inventory_or_demand", ("庫存", "存貨", "需求", "去化", "客戶拉貨", "inventory", "demand"), ("inventory_growth_yoy", "revenue_growth_yoy", "cash_conversion_ratio")),
    ("revenue_or_orders", ("營收", "訂單", "接單", "客戶", "revenue", "orders"), ("revenue_growth_yoy", "gross_margin", "operating_margin")),
    ("financial_outlook", ("展望", "財測", "預估", "forecast", "outlook", "guidance"), ("revenue_growth_yoy", "operating_margin", "cash_conversion_ratio")),
    ("financing_or_debt", ("借款", "公司債", "現金增資", "資金", "負債", "financing", "debt"), ("debt_ratio", "current_ratio", "free_cash_flow")),
    ("ma_or_investment", ("併購", "投資", "取得", "處分", "investment", "acquisition"), ("free_cash_flow", "debt_ratio", "capex_intensity")),
    ("operation_disruption", ("停工", "停產", "火災", "地震", "斷電", "營運", "disruption"), ("revenue_growth_yoy", "operating_cash_flow")),
    ("legal_or_penalty", ("訴訟", "裁罰", "罰款", "違反", "litigation", "penalty"), ("net_margin", "operating_cash_flow")),
    ("governance", ("董事", "總經理", "治理", "內控", "governance"), ("debt_ratio", "current_ratio")),
)


def _require_company(ticker: str):
    company = get_company(ticker)
    if company is None:
        raise UnsupportedCompanyError("MVP 僅分析已登錄的半導體公司；請先將公司加入 semiconductor registry。")
    return company


def investor_conference_query_url(ticker: str) -> str:
    # MOPS 法說會查詢入口常見路徑為 t100sb07_1。以 query URL 保存資料來源，
    # 後續正式 scraper 可再依 MOPS 表單欄位補強 POST/HTML parsing。
    params = urlencode({"co_id": ticker, "firstin": "true", "step": "1"})
    return f"{MOPS_BASE}/t100sb07_1?{params}"


def material_event_query_url(ticker: str, year: int | None = None) -> str:
    params = {"co_id": ticker, "firstin": "true", "step": "1"}
    if year is not None:
        params["year"] = str(year)
    return f"{MOPS_BASE}/t05st01?{urlencode(params)}"


def build_investor_conference_metadata(ticker: str, *, max_items: int = 3) -> list[InvestorConferenceRecord]:
    company = _require_company(ticker)
    url = investor_conference_query_url(company.ticker)
    related_metrics = CONFERENCE_TOPIC_METRICS.get(company.subindustry, [])
    topics = [
        "近期營運展望",
        "資本支出與產能規劃" if company.subindustry == "晶圓代工" else "產品組合與需求變化",
        "庫存、現金流與財務結構",
    ]
    record = InvestorConferenceRecord(
        ticker=company.ticker,
        company_name=company.name,
        subindustry=company.subindustry,
        title=f"{company.name} 法人說明會資料查詢入口",
        source_url=url,
        status="metadata_only",
        extracted_topics=topics[:max_items],
        related_metrics=related_metrics,
        limitations=[
            "目前為 Phase 4 metadata MVP：先保存 MOPS 法說會查詢入口與子產業關聯指標，尚未解析 PDF 或影音逐字稿。",
            "正式 scraper 需依 MOPS 表單與各公司申報附件欄位補充文件 URL、日期與簡報文字。",
        ],
    )
    return [record]


def classify_material_event(title: str, raw_text: str | None = None) -> tuple[MaterialEventCategory, list[str], bool]:
    text = f"{title} {raw_text or ''}".casefold()
    for category, keywords, metrics in MATERIAL_EVENT_KEYWORDS:
        if any(keyword.casefold() in text for keyword in keywords):
            return category, list(metrics), True
    return "other", [], False


def build_material_event_metadata(
    ticker: str,
    *,
    year: int | None = None,
    title: str | None = None,
    raw_text: str | None = None,
) -> list[MaterialEventRecord]:
    company = _require_company(ticker)
    source_url = material_event_query_url(company.ticker, year=year)
    event_title = title or f"{company.name} 歷史重大訊息查詢入口"
    category, related_metrics, risk_related = classify_material_event(event_title, raw_text)
    return [
        MaterialEventRecord(
            ticker=company.ticker,
            company_name=company.name,
            subindustry=company.subindustry,
            title=event_title,
            category=category,
            source_url=source_url,
            status="metadata_only",
            raw_text=raw_text,
            related_metrics=related_metrics,
            risk_related=risk_related,
            limitations=[
                "目前為 Phase 5 metadata MVP：先保存 MOPS 重大訊息查詢入口與事件分類規則，尚未批次解析歷史公告清單。",
                "事件分類使用保守關鍵字與子產業指標對應，後續需以 MOPS 實際公告文字與 Gemini 摘要校驗。",
            ],
        )
    ]
