import json
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

DATA_PATH = Path('/app/data')


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

        # --- Создание пользователей ---
        self.stdout.write('Создание пользователей...')
        with open(DATA_PATH / 'users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        for user_data in users_data:
            User.objects.create_user(**user_data)
        self.stdout.write(self.style.SUCCESS('Пользователи созданы.'))

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

        # --- Загрузка рецептов ---
        self.stdout.write('Загрузка рецептов...')
        with open(DATA_PATH / 'recipes.json', 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)

        for recipe_data in recipes_data:
            author = User.objects.get(username=recipe_data['author_username'])
            tags = Tag.objects.filter(name__in=recipe_data['tags'])
            ingredients_data = recipe_data.pop('ingredients')

            recipe = Recipe.objects.create(
                author=author,
                name=recipe_data['name'],
                text=recipe_data['text'],
                cooking_time=recipe_data['cooking_time']
            )

            image_path = DATA_PATH / 'images' / recipe_data['image']
            with open(image_path, 'rb') as img_file:
                recipe.image.save(recipe_data['image'], File(img_file), save=True)

            recipe.tags.set(tags)
            
            recipe_ingredients = []
            for ing_data in ingredients_data:
                ingredient = Ingredient.objects.get(
                    name=ing_data['name'],
                    measurement_unit=ing_data['measurement_unit']
                )
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=ing_data['amount']
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        self.stdout.write(self.style.SUCCESS('Все данные успешно загружены!'))
