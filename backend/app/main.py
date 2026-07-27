from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.financial import router as financial_router

app = FastAPI(
    title="FinTrust Alert Financial Rule Engine API",
    version="0.2.0",
    description=(
        "半導體產業財報抓取、財務指標計算與版本化規則分析 MVP。"
        "本服務不提供投資建議。"
    ),
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(financial_router)


@app.get("/")
def root():
    return {
        "service": "FinTrust Alert Financial Rule Engine API",
        "version": "0.2.0",
        "docs": "/docs",
        "live_endpoint": "/api/v1/financial/statements/2330/analyze",
        "disclaimer": "僅供財報分析與可信度風險提醒，非投資建議。",
    }
