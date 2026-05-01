FROM python:3.13.13-alpine3.23

WORKDIR /content

RUN apk add --no-cache curl \
    && addgroup -S readmeclientgroup \
    && adduser -S -G readmeclientgroup -h /home/readmeclientuser -s /sbin/nologin readmeclientuser

ENV PYTHONBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/readmeclientuser/.local/bin:$PATH" \
    PYTHONPATH=/content

USER readmeclientuser

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=readmeclientuser:readmeclientgroup . ./client/

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/client_healthcheck || exit 1

WORKDIR /content/client

EXPOSE 8000

CMD ["uvicorn", "main:client_app", "--host", "0.0.0.0", "--port", "8000"]