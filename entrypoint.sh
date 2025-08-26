#!/bin/bash

# Простой и надежный цикл ожидания PostgreSQL с помощью netcat
echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
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