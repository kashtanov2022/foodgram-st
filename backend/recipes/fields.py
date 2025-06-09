# backend/recipes/fields.py
import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    Кастомное поле для обработки изображений, закодированных в Base64.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):

            # Разделяем строку на формат и само изображение
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            # Генерируем уникальное имя файла
            file_name = f'{uuid.uuid4()}.{ext}'

            # Декодируем и создаем ContentFile
            data = ContentFile(base64.b64decode(imgstr), name=file_name)

        return super().to_internal_value(data)
