FROM python:3.13-slim

WORKDIR /client

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN groupadd readmeservergroup -r && useradd -r -m -g readmeservergroup -s /sbin/nologin readmeserveruser

ENV PYTHONBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/home/readmeserveruser/.local/bin:$PATH"

USER readmeserveruser

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=readmeserveruser:readmeservergroup . .

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/server_healthcheck || exit 1

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]