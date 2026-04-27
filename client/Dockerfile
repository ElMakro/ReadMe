FROM python:3.13-slim

WORKDIR /content

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN groupadd readmeclientgroup -r && useradd -r -m -g readmeclientgroup -s /sbin/nologin readmeclientuser

ENV PYTHONBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/home/readmeclientuser/.local/bin:$PATH"

USER readmeclientuser

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=readmeclientuser:readmeclientgroup . ./client/

WORKDIR /content/client

ENV PYTHONPATH=/content

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/client_healthcheck || exit 1

EXPOSE 8000

CMD ["uvicorn", "client.main:client_app", "--host", "0.0.0.0", "--port", "8000"]