# Инструкция по выполнению бэкапов БД

1. Если с БД всё нормально, то ничего не трогайте - бэкапы выполняются автоматически каждые 12 часов. Срок хранения
   бэкапов - 7 дней.
2. Если нужно провести ручной бэкап, то необходимо выполнить команды:
    - Для сохранения в виртуальный том Docker: `docker exec readme_postgres_backups /usr/local/bin/backup`
    - Для сохранения на компьютер:
      `docker exec -t readme_postgres_db pg_dump -U readmepguser -d readmedb | gzip > manual_backup_$(date +%Y-%m-%d_%H%M%S).sql.gz`
3. Если необходимо восстановить БД из бэкапа:
    1. Остановите контейнеры, которые могут писать в БД: `docker compose stop client` или `docker stop readme_client`
    2. Выберите нужный файл: `docker exec readme_postgres_backups ls -l /backups`
        - Учтите, что в этом каталоге есть несколько подкаталогов, различающихся по периодичности бэкапов;
    3. Очистите текущую схему:
       `docker exec -it readme_postgres_db psql -U readmepguser -d readmedb -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"`
    4. Примените бэкап (вставьте нужный файл):
       `docker exec -i readme_postgres_backups gunzip -c /backups/НУЖНЫЙ_КАТАЛОГ/ИМЯ_ФАЙЛА.sql.gz | docker exec -i readme_postgres_db psql -U readmepguser -d readmedb`
    5. Запустите контейнеры: `docker compose start client` или `docker start readme_client`