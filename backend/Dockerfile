FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MOPS_XBRL_CACHE_DIR=/tmp/fintrust/mops_ixbrl_cache \
    MOPS_XBRL_CACHE_TTL_HOURS=24 \
    FINANCIAL_DATABASE_PATH=/tmp/fintrust/financial_facts.sqlite3

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY app ./app

RUN mkdir -p /tmp/fintrust/mops_ixbrl_cache

EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
