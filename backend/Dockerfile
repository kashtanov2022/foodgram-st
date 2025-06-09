# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости системы
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в рабочую директорию
COPY ./backend /app/

# --- ДОБАВЛЕНО: Копируем директорию с данными ---
COPY ./data /app/data/

# Копируем скрипт запуска и делаем его исполняемым
COPY ./backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Указываем, что наш скрипт будет точкой входа
ENTRYPOINT ["/app/entrypoint.sh"]

# Команда по умолчанию для Gunicorn
CMD ["gunicorn", "configuration.wsgi:application", "--bind", "0.0.0.0:8000"]
