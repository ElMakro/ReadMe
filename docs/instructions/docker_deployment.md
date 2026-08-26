# Инструкция по развёртыванию проекта

1. Установить пакеты `docker`: 
   - `sudo apt update`
   - `sudo apt install docker`
2. Сформировать файл `.env` по образцу `.env.example`
3. Развернуть контейнеры при помощи оркестратора Docker Compose c подходящим конфигурационным файлом:
   - Если необходимо запустить в окружении разработки, то `docker compose -f docker-compose.dev.yml up`
   - Если необходимо развернуть в производственном окружении, то `docker compose -f docker-compose.prod.yml up`
4. Выполнить подключение к контейнеру через `DBeaver`, используя параметры из `.env`.
5. Остановка контейнера: `docker compose -f {запущенный конфигурационный файл} down --volumes` - удалит контейнеры и тома.

Полезное: [тут](https://selectel.ru/blog/docker-compose/).