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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создаем директорию приложения заранее, чтобы не было проблем с WORKDIR
RUN mkdir -p /app/backend
RUN mkdir -p /app/data

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app/backend

# Копируем файл зависимостей бэкенда (из корня контекста в /app/backend/requirements.txt)
COPY requirements.txt /app/backend/requirements.txt

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код бэкенда (из папки backend/ в корне контекста)
COPY backend/ /app/backend/

# Собираем статические файлы
RUN python manage.py collectstatic --noinput --clear

# Копируем данные для инициализации
COPY data/ingredients.json /app/data/ingredients.json

# Создаем директории для статики и медиа внутри /app/backend/
RUN mkdir -p /app/backend/media_volume/
