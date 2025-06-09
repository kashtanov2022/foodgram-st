#!/bin/sh

# Ожидание доступности базы данных
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Применяем миграции базы данных
echo "Applying database migrations..."
python manage.py migrate

# Собираем статические файлы
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear


# Запускаем основной процесс (Gunicorn)
exec "$@"