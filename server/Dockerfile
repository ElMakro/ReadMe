FROM python:3.13-alpine3.23

WORKDIR /content

RUN apk add --no-cache \
    curl \
    bash \
    && addgroup -S readmeservergroup \
    && adduser -S -G readmeservergroup -h /home/readmeserveruser -s /sbin/nologin readmeserveruser

RUN apk add --no-cache openjdk21-jre \
    graphviz

RUN apk add --no-cache \
    perl \
    wget \
    tar \
    fontconfig \
    && wget https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz \
    && tar xzf install-tl-unx.tar.gz \
    && cd install-tl-* \
    && echo "selected_scheme scheme-basic" > texlive.profile \
    && echo "option_doc 0" >> texlive.profile \
    && echo "option_src 0" >> texlive.profile \
    && ./install-tl --profile=texlive.profile \
    && cd / \
    && rm -rf /tmp/install-tl-* \
    && rm install-tl-unx.tar.gz

ENV PATH="/usr/local/texlive/2026/bin/x86_64-linux:${PATH}"

RUN tlmgr install \
    latex \
    tools \
    amsmath \
    amscls \
    graphics \
    geometry \
    fontspec \
    unicode-math \
    && tlmgr path add

RUN pip install --no-cache-dir latex

RUN curl -L -o /opt/plantuml.jar https://github.com/plantuml/plantuml/releases/download/v1.2026.3/plantuml-1.2026.3.jar

ENV PYTHONBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/readmeserveruser/.local/bin:$PATH" \
    PYTHONPATH=/content \
    PLANTUML_JAR_PATH=/opt/plantuml.jar

RUN mkdir -p server/data/content && chown readmeserveruser:readmeservergroup server/data/content

USER readmeserveruser

COPY --chown=readmeserveruser:readmeservergroup requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=readmeserveruser:readmeservergroup . ./server/

WORKDIR /content/server

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/server_healthcheck || exit 1

EXPOSE $SERVER_PORT

CMD uvicorn main:app --host 0.0.0.0 --port $SERVER_PORT