FROM python:3.13.13-alpine3.23

WORKDIR /content

RUN apk add --no-cache curl \
    && addgroup -S readmeservergroup \
    && adduser -S -G readmeservergroup -h /home/readmeserveruser -s /sbin/nologin readmeserveruser

ENV PYTHONBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/readmeserveruser/.local/bin:$PATH" \
    PYTHONPATH=/content

USER readmeserveruser

COPY --chown=readmeserveruser:readmeservergroup . ./server/

WORKDIR /content/server

RUN pip install --no-cache-dir --user -r requirements.txt

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/server_healthcheck || exit 1

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]