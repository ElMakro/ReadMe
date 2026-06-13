FROM python:3.13-alpine3.23

WORKDIR /content

RUN addgroup -g 1000 readme_database_manager_group \
    && adduser -D -u 1000 -G readme_database_manager_group -h /home/readme_database_manager_user -s /sbin/nologin readme_database_manager_user

RUN apk add --no-cache postgresql-client curl tar gzip

RUN mkdir -p /backups \
    && mkdir -p /content/server/data/courses_resources/resources \
    && mkdir -p /content/server/data/users_resources/resources

RUN chown -R readme_database_manager_user:readme_database_manager_group /backups \
    && chown -R readme_database_manager_user:readme_database_manager_group /content/server/data

COPY database_manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/content \
    PYTHONUNBUFFERED=1 \
    ALEMBIC_CONFIG=/content/alembic.ini

COPY alembic.ini /content/

COPY server/app/api/v1/auth/auth_handler.py /content/server/app/api/v1/auth/auth_handler.py
COPY server/app/api/v1/users/users.py /content/server/app/api/v1/users/users.py
COPY server/app/api/v1/exceptions.py /content/server/app/api/v1/exceptions.py
COPY server/app/common_dependencies/utils.py /content/server/app/common_dependencies/utils.py
COPY server/database /content/server/database
COPY server/enums /content/server/enums
COPY server/config /content/server/config
COPY server/data /content/server/data
COPY database_manager/database_manager.py /content/scripts/database_manager.py

RUN chown -R readme_database_manager_user:readme_database_manager_group /content

RUN chmod +x /content/scripts/database_manager.py

USER readme_database_manager_user

WORKDIR /content/scripts

ENTRYPOINT ["python", "/content/scripts/database_manager.py"]