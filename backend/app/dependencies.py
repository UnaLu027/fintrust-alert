from __future__ import annotations

import os
from functools import lru_cache

from app.services.fact_repository import FinancialFactRepository


@lru_cache(maxsize=1)
def get_fact_repository() -> FinancialFactRepository:
    path = os.getenv("FINANCIAL_DATABASE_PATH", "./data/financial_facts.sqlite3")
    return FinancialFactRepository(path)
