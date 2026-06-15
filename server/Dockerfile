FROM python:3.13-alpine3.23

WORKDIR /content

RUN addgroup -g 1000 readme_server_group \
    && adduser -D -u 1000 -G readme_server_group -h /home/readme_server_user -s /sbin/nologin readme_server_user

RUN apk add --no-cache curl bash

RUN apk add --no-cache openjdk21-jre graphviz

RUN curl -L -o /opt/plantuml.jar https://github.com/plantuml/plantuml/releases/download/v1.2026.3/plantuml-1.2026.3.jar

ENV PYTHONBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/content \
    PLANTUML_JAR_PATH=/opt/plantuml.jar

RUN mkdir -p /content/server/data/courses_resources/resources \
    && mkdir -p /content/server/data/users_resources/resources

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=readme_server_user:readme_server_group . ./server/

RUN chown -R readme_server_user:readme_server_group /content/server/data

USER readme_server_user

WORKDIR /content/server

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$SERVER_PORT/api/healthcheck || exit 1

EXPOSE $SERVER_PORT

CMD uvicorn main:app --host $SERVER_HOST --port $SERVER_PORT