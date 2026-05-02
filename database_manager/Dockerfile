FROM python:3.13.13-alpine

WORKDIR /content

RUN apk add --no-cache \
    postgresql-client \
    curl

COPY database_manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/content \
    PYTHONUNBUFFERED=1 \
    ALEMBIC_CONFIG=/content/alembic.ini \
    PATH="/content/scripts:$PATH"

COPY database_manager/scripts /content/scripts
RUN chmod +x /content/scripts/* && \
    dos2unix /content/scripts/* 2>/dev/null || true

COPY alembic.ini /content/

WORKDIR /content/server

COPY server/.env .env
COPY server/database database
COPY server/config config
COPY server/enums enums

WORKDIR /content/scripts

ENTRYPOINT ["database_manager"]
CMD []