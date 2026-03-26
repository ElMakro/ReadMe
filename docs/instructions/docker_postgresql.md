# Инструкция по разворачиванию Docker-контейнера СУБД PostgreSQL

1. Установить пакеты `docker`: 
   - 'sudo apt update'
   - `sudo apt install docker`
2. Перейти в каталог `docker`: `cd docker`
3. Выполнить разворачивание Docker-контейнера при помощи оркестратора Docker Compose: `sudo docker-compose up -d`.
    - Параметр `-d` отвечает за работу в фоновом режиме, возможно его стоит убирать, чтобы можно было посмотреть логи.
4. Выполнить подключение к контейнеру через `DBeaver`:
   - Хост: `localhost` (значение по умолчанию);
   - Порт: `5432` (значение по умолчанию);
   - БД: `readmedb`;
   - Пользователь: `readmepguser`;
   - Пароль: `pgpwd4readme`;
5. Остановка контейнера: `docker-compose down --volumes` - удалит контейнеры и тома.

Полезное: [тут](https://selectel.ru/blog/docker-compose/).