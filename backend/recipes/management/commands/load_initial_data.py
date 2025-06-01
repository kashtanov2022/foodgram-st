import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files.images import ImageFile

from recipes.models import Ingredient, Tag, Recipe, AmountIngredient

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Loads initial data (tags, ingredients, users, recipes) '
        'into the database'
    )

    DEFAULT_TAGS = [
        {'name': 'Завтрак', 'color': '#49B64E', 'slug': 'breakfast'},
        {'name': 'Обед', 'color': '#E26C2D', 'slug': 'lunch'},
        {'name': 'Ужин', 'color': '#8775D2', 'slug': 'dinner'},
        {'name': 'Перекус', 'color': '#F0DB4F', 'slug': 'snack'},
        {'name': 'Десерт', 'color': '#FF69B4', 'slug': 'dessert'},
        {'name': 'Выпечка', 'color': '#A52A2A', 'slug': 'baking'},
        {'name': 'Напитки', 'color': '#00BFFF', 'slug': 'drinks'},
    ]

    def _load_json_data(self, file_name):
        """Вспомогательный метод для загрузки данных из JSON файла."""
        file_path = os.path.join(
            settings.BASE_DIR.parent, 'data', file_name
        )
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(
                f'Error decoding JSON from {file_path}.'
            ))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error reading {file_path}: {e}'
            ))
            return None

    @transaction.atomic
    def handle(self, *args, **options):
        """Обработчик загрузки изначальных данных в базу."""
        self.stdout.write(
            self.style.SUCCESS('Starting data loading process...')
        )

        # 1. Загружаем теги
        self.stdout.write(self.style.HTTP_INFO('Loading tags...'))
        tags_created_count = 0
        tags_skipped_count = 0
        for tag_data in self.DEFAULT_TAGS:
            tag, created = Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults={
                    'name': tag_data['name'], 'color': tag_data['color']
                }
            )
            if created:
                tags_created_count += 1
            else:
                tags_skipped_count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Tags loading complete. Created: {tags_created_count}, '
            f'Skipped: {tags_skipped_count}.'
        ))

        # 2. Загружаем ингредиенты
        self.stdout.write(self.style.HTTP_INFO('Loading ingredients...'))
        ingredients_data_list = self._load_json_data('ingredients.json')
        ingredients_created_count = 0
        ingredients_skipped_count = 0
        ingredients_errors_count = 0

        if ingredients_data_list:
            for item in ingredients_data_list:
                name = item.get('name')
                measurement_unit = item.get('measurement_unit')

                if not name or not measurement_unit:
                    self.stdout.write(self.style.WARNING(
                        f'Skipping ingredient due to missing name or '
                        f'measurement_unit: {item}'
                    ))
                    ingredients_errors_count += 1
                    continue
                try:
                    _, created = Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit,
                    )
                    if created:
                        ingredients_created_count += 1
                    else:
                        ingredients_skipped_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Error creating ingredient "{name}": {e}'
                    ))
                    ingredients_errors_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Ingredients loading complete. '
                f'Created: {ingredients_created_count}, '
                f'Skipped: {ingredients_skipped_count}, '
                f'Errors: {ingredients_errors_count}.'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'Skipped loading ingredients due to file issues.'
            ))

        # 3. Загружаем пользователей
        self.stdout.write(self.style.HTTP_INFO('Loading users...'))
        users_data_list = self._load_json_data('users.json')
        users_created_count = 0
        users_skipped_count = 0
        users_errors_count = 0

        if users_data_list:
            for user_data in users_data_list:
                username = user_data.get('username')
                if not username:
                    self.stdout.write(self.style.WARNING(
                        f'Skipping user due to missing username: {user_data}'
                    ))
                    users_errors_count += 1
                    continue
                try:
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': user_data.get('email'),
                            'first_name': user_data.get('first_name', ''),
                            'last_name': user_data.get('last_name', ''),
                        }
                    )
                    if created:
                        user.set_password(user_data.get('password'))
                        user.save()
                        users_created_count += 1
                    else:
                        users_skipped_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Error creating user "{username}": {e}'
                    ))
                    users_errors_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Users loading complete. '
                f'Created: {users_created_count}, '
                f'Skipped: {users_skipped_count}, '
                f'Errors: {users_errors_count}.'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'Skipped loading users due to file issues.'
            ))

        # 4. Загружаем рецепты
        self.stdout.write(self.style.HTTP_INFO('Loading recipes...'))
        recipes_data_list = self._load_json_data('recipes.json')
        recipes_created_count = 0
        recipes_skipped_count = 0
        recipes_errors_count = 0

        images_base_dir_in_container = '/app/data/images'

        if recipes_data_list:
            for recipe_data in recipes_data_list:
                author_username = recipe_data.get('author_username')
                recipe_name = recipe_data.get('name')

                if not author_username or not recipe_name:
                    self.stdout.write(self.style.WARNING(
                        f'Skipping recipe: missing author/name: '
                        f'{recipe_name or "N/A"}'
                    ))
                    recipes_errors_count += 1
                    continue
                try:
                    author = User.objects.get(username=author_username)
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f'Author "{author_username}" not found for '
                        f'"{recipe_name}". Skipping.'
                    ))
                    recipes_errors_count += 1
                    continue

                recipe, created = Recipe.objects.get_or_create(
                    author=author,
                    name=recipe_name,
                    defaults={
                        'text': recipe_data.get('text', ''),
                        'cooking_time': recipe_data.get('cooking_time', 1)
                    }
                )

                if created:
                    # Добавляем изображение
                    image_path_in_json = recipe_data.get('image')
                    if image_path_in_json:
                        image_filename = os.path.basename(image_path_in_json)
                        source_image_full_path = os.path.join(
                            images_base_dir_in_container, image_filename
                        )

                        if os.path.exists(source_image_full_path):
                            try:
                                with open(
                                    source_image_full_path, 'rb'
                                ) as img_file:
                                    recipe.image.save(
                                        image_filename,
                                        ImageFile(img_file),
                                        save=True
                                    )
                            except Exception as e_img:
                                self.stdout.write(self.style.ERROR(
                                    f'Error saving image for recipe '
                                    f'"{recipe_name}": {e_img}'
                                ))
                                recipes_errors_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(
                                f'Source image file not found: '
                                f'{source_image_full_path} for recipe '
                                f'"{recipe_name}". Skipping image.'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'No image path in JSON for recipe '
                            f'"{recipe_name}".'
                        ))

                    # Добавляем теги
                    tag_slugs = recipe_data.get('tags', [])
                    for slug in tag_slugs:
                        try:
                            tag_obj = Tag.objects.get(slug__iexact=slug)
                            recipe.tags.add(tag_obj)
                        except Tag.DoesNotExist:
                            try:
                                tag_obj = Tag.objects.get(name__iexact=slug)
                                recipe.tags.add(tag_obj)
                            except Tag.DoesNotExist:
                                self.stdout.write(self.style.WARNING(
                                    f'Tag "{slug}" not found for recipe '
                                    f'"{recipe_name}". Skipping tag.'
                                ))

                    # Добавляем ингредиенты
                    ingredients_in_recipe = recipe_data.get('ingredients', [])
                    for ing_data in ingredients_in_recipe:
                        ing_name = ing_data.get('name')
                        ing_unit = ing_data.get('measurement_unit')
                        ing_amount = ing_data.get('amount')

                        if not all([ing_name, ing_unit, ing_amount]):
                            self.stdout.write(self.style.WARNING(
                                f'Skipping ingredient in '
                                f'recipe "{recipe_name}" '
                                f'due to missing data: {ing_data}'
                            ))
                            continue
                        try:
                            ingredient_obj = Ingredient.objects.get(
                                name__iexact=ing_name,
                                measurement_unit__iexact=ing_unit
                            )
                            AmountIngredient.objects.create(
                                recipe=recipe,
                                ingredient=ingredient_obj,
                                amount=ing_amount
                            )
                        except Ingredient.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f'Ingredient "{ing_name} '
                                f'({ing_unit})" not found '
                                f'for recipe "{recipe_name}". '
                                f'Skipping ingredient.'
                            ))
                        except Exception as e_amount:
                            self.stdout.write(self.style.ERROR(
                                f'Error adding ingredient '
                                f'"{ing_name}" to recipe '
                                f'"{recipe_name}": {e_amount}'
                            ))
                    recipes_created_count += 1
                else:
                    recipes_skipped_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Recipes loading complete. '
                f'Created: {recipes_created_count}, '
                f'Skipped: {recipes_skipped_count}, '
                f'Errors: {recipes_errors_count}.'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'Skipped loading recipes due to file issues.'
            ))

        self.stdout.write(
            self.style.SUCCESS('Initial data loading finished!')
        )
