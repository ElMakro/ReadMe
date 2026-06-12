FROM python:3.13-alpine3.23

WORKDIR /content

RUN apk add --no-cache \
    postgresql-client \
    curl \
    tar \
    gzip

COPY database_manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/content \
    PYTHONUNBUFFERED=1 \
    ALEMBIC_CONFIG=/content/alembic.ini

COPY alembic.ini /content/

COPY server/app/api/v1/auth/auth_handler.py /content/server/app/api/v1/auth/auth_handler.py
COPY server/app/api/v1/users/users.py /content/server/app/api/v1/users/users.py
COPY server/app/api/v1/exceptions.py /content/server/app/api/v1/exceptions.py
COPY server/database /content/server/database
COPY server/enums /content/server/enums
COPY server/config /content/server/config
COPY server/app/common_dependencies/utils.py /content/server/app/common_dependencies/utils.py
COPY server/data /content/server/data

COPY database_manager/database_manager.py /content/scripts/database_manager.py
RUN chmod +x /content/scripts/database_manager.py

WORKDIR /content/scripts

ENTRYPOINT ["python", "/content/scripts/database_manager.py"]