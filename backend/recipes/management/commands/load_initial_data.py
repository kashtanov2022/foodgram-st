import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient, Tag # Убедитесь, что модели импортируются правильно


class Command(BaseCommand):
    help = 'Loads initial data (ingredients and tags) into the database'

    # Определим начальные теги здесь
    # Вы можете расширить этот список или изменить цвета/слаги
    DEFAULT_TAGS = [
        {'name': 'Завтрак', 'color': '#49B64E', 'slug': 'breakfast'}, # Зеленый
        {'name': 'Обед', 'color': '#E26C2D', 'slug': 'lunch'},       # Оранжевый
        {'name': 'Ужин', 'color': '#8775D2', 'slug': 'dinner'},      # Фиолетовый
        {'name': 'Перекус', 'color': '#F0DB4F', 'slug': 'snack'},     # Желтый
        {'name': 'Десерт', 'color': '#FF69B4', 'slug': 'dessert'},    # Розовый
        {'name': 'Выпечка', 'color': '#A52A2A', 'slug': 'baking'},    # Коричневый
        {'name': 'Напитки', 'color': '#00BFFF', 'slug': 'drinks'},    # Голубой
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data loading process...'))

        # --- Загрузка Тегов ---
        self.stdout.write(self.style.HTTP_INFO('Loading tags...'))
        tags_created_count = 0
        tags_skipped_count = 0
        for tag_data in self.DEFAULT_TAGS:
            tag, created = Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults={'name': tag_data['name'], 'color': tag_data['color']}
            )
            if created:
                tags_created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Tag "{tag.name}" created.'))
            else:
                tags_skipped_count += 1
                # self.stdout.write(self.style.WARNING(f'Tag "{tag.name}" already exists. Skipped.'))
        self.stdout.write(self.style.SUCCESS(
            f'Tags loading complete. Created: {tags_created_count}, Skipped: {tags_skipped_count}.'
        ))

        # --- Загрузка Ингредиентов ---
        # Путь к файлу ingredients.json относительно папки data в корне проекта
        ingredients_file_path = os.path.join(settings.BASE_DIR.parent, 'data', 'ingredients.json')
        # settings.BASE_DIR у нас указывает на папку backend/, поэтому .parent для корня проекта

        if not os.path.exists(ingredients_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {ingredients_file_path}'))
            self.stdout.write(self.style.ERROR('Please make sure ingredients.json is in the "data" directory at the project root.'))
            return

        self.stdout.write(self.style.HTTP_INFO(f'Loading ingredients from {ingredients_file_path}...'))
        try:
            with open(ingredients_file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Error decoding JSON from {ingredients_file_path}. Make sure it is a valid JSON file.'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred while opening or reading {ingredients_file_path}: {e}'))
            return

        ingredients_created_count = 0
        ingredients_skipped_count = 0
        ingredients_errors_count = 0

        for item in ingredients_data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not measurement_unit:
                self.stdout.write(self.style.WARNING(
                    f'Skipping ingredient due to missing name or measurement_unit: {item}'
                ))
                ingredients_errors_count +=1
                continue

            try:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name.lower(), # Приводим имя к нижнему регистру для большей уникальности
                    measurement_unit=measurement_unit.lower(), # и единицу измерения тоже
                    # Если хотите сохранить оригинальный регистр, используйте:
                    # name=name,
                    # measurement_unit=measurement_unit,
                    # defaults={'name': name, 'measurement_unit': measurement_unit}
                    # Однако, это может привести к дублям типа "Соль" и "соль"
                )
                if created:
                    ingredients_created_count += 1
                    # self.stdout.write(self.style.SUCCESS(f'Ingredient "{ingredient.name}" created.'))
                else:
                    ingredients_skipped_count += 1
                    # self.stdout.write(self.style.WARNING(f'Ingredient "{ingredient.name}, {ingredient.measurement_unit}" already exists. Skipped.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error creating ingredient "{name}": {e}'
                ))
                ingredients_errors_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Ingredients loading complete. Created: {ingredients_created_count}, '
            f'Skipped (already exist): {ingredients_skipped_count}, '
            f'Errors/Invalid entries: {ingredients_errors_count}.'
        ))
        self.stdout.write(self.style.SUCCESS('Initial data loading finished!'))