FROM python:3.13-alpine3.23

WORKDIR /content

RUN addgroup -g 1000 readme_client_group \
    && adduser -D -u 1000 -G readme_client_group -h /home/readme_client_user -s /sbin/nologin readme_client_user

RUN apk add --no-cache curl

ENV PYTHONBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/content

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=readme_client_user:readme_client_group . ./client/

USER readme_client_user

WORKDIR /content/client

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${CLIENT_PORT}/client_healthcheck || exit 1

EXPOSE $CLIENT_PORT

CMD uvicorn main:client_app --host $CLIENT_HOST --port $CLIENT_PORT