import json

import httpx
import pytest

from app.services.twse_openapi import TwseOpenApiClient


@pytest.mark.asyncio
async def test_fetch_company_bundle_filters_rows_by_ticker():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = [
            {"公司代號": "2303", "公司名稱": "聯電"},
            {"公司代號": "2330", "公司名稱": "台積電", "path": request.url.path},
        ]
        return httpx.Response(200, content=json.dumps(payload).encode("utf-8"))

    client = TwseOpenApiClient(transport=httpx.MockTransport(handler))
    bundle = await client.fetch_company_bundle("2330")

    assert bundle["income_statement"]["公司名稱"] == "台積電"
    assert bundle["balance_sheet"]["公司代號"] == "2330"
    assert bundle["monthly_revenue"]["公司代號"] == "2330"
