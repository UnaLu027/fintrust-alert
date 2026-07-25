from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.financial import router as financial_router

app = FastAPI(
    title="FinTrust Alert Financial Evidence API",
    version="0.1.0",
    description=(
        "半導體產業財務主張抽取與官方財報確定性重算 MVP。"
        "本服務不提供投資建議。"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(financial_router)


@app.get("/")
def root():
    return {
        "service": "FinTrust Alert Financial Evidence API",
        "docs": "/docs",
        "disclaimer": "僅供資訊查證與可信度風險提醒，非投資建議。",
    }
