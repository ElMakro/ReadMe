FROM python:3.13-alpine3.23

WORKDIR /content

RUN apk add --no-cache \
    curl \
    bash \
    && addgroup -S readmeservergroup \
    && adduser -S -G readmeservergroup -h /home/readmeserveruser -s /sbin/nologin readmeserveruser

RUN apk add --no-cache openjdk21-jre \
    graphviz

RUN curl -L -o /opt/plantuml.jar https://github.com/plantuml/plantuml/releases/download/v1.2026.3/plantuml-1.2026.3.jar

ENV PYTHONBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/readmeserveruser/.local/bin:$PATH" \
    PYTHONPATH=/content \
    PLANTUML_JAR_PATH=/opt/plantuml.jar

USER readmeserveruser

COPY --chown=readmeserveruser:readmeservergroup requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=readmeserveruser:readmeservergroup . ./server/

WORKDIR /content/server

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/server_healthcheck || exit 1

EXPOSE $SERVER_PORT

CMD uvicorn main:app --host $SERVER_HOST --port $SERVER_PORT