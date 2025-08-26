#!/bin/bash

# Устанавливаем переменные для подключения к БД из .env
# (Docker Compose передаст их в контейнер)
export PGPASSWORD=$DB_PASSWORD

# Более надежный цикл ожидания PostgreSQL
echo "Waiting for postgres..."
until psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "PostgreSQL started"

# Накатываем миграции базы данных
echo "Running database migrations..."
alembic upgrade head

# Запускаем бота
echo "Starting bot..."
exec python -m app.bot