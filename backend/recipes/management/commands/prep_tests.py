import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import Ingredient, Recipe, Tag
from users.models import User

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATA_PATH = BASE_DIR / 'data'


class Command(BaseCommand):
    help = 'Загрузка тестовых данных из JSON файлов'

    @transaction.atomic
    def handle(self, *args, **options):
        # --- Очистка базы данных ---
        self.stdout.write(self.style.WARNING('Начало очистки базы данных...'))
        User.objects.filter(is_superuser=False).delete()
        Recipe.objects.all().delete()
        Tag.objects.all().delete()
        Ingredient.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('База данных очищена.'))

        # --- Создание тегов ---
        self.stdout.write('Создание тегов...')
        tags_data = [
            {'name': 'завтрак', 'color': '#E26C2D', 'slug': 'breakfast'},
            {'name': 'обед', 'color': '#49B64E', 'slug': 'lunch'},
            {'name': 'ужин', 'color': '#8775D2', 'slug': 'dinner'},
            {'name': 'перекус', 'color': '#3399FF', 'slug': 'snack'},
            {'name': 'десерт', 'color': '#FF66CC', 'slug': 'dessert'},
            {'name': 'выпечка', 'color': '#FFCC66', 'slug': 'bakery'},
        ]
        Tag.objects.bulk_create([Tag(**data) for data in tags_data])
        self.stdout.write(self.style.SUCCESS('Теги созданы.'))

        # --- Загрузка ингредиентов ---
        self.stdout.write('Загрузка ингредиентов...')
        with open(DATA_PATH / 'ingredients.json', 'r', encoding='utf-8') as f:
            ingredients_data = json.load(f)
        Ingredient.objects.bulk_create(
            [Ingredient(**data) for data in ingredients_data]
        )
        self.stdout.write(self.style.SUCCESS('Ингредиенты загружены.'))

        self.stdout.write(self.style.SUCCESS('Все данные успешно загружены!'))
