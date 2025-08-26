# 1. Берем официальный, легкий образ Python
FROM python:3.12-slim

# 2. Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# --- ИЗМЕНЕНИЕ ---
# Устанавливаем netcat, который нужен для проверки доступности БД
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd

# 3. Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем весь остальной код проекта в контейнер
COPY . .

# 5. Делаем наш скрипт-запускатор исполняемым
RUN chmod +x /app/entrypoint.sh

# 6. Указываем, что при старте контейнера нужно запустить этот скрипт
ENTRYPOINT ["/app/entrypoint.sh"]