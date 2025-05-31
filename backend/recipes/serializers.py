from django.db import transaction
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField  # Установим эту библиотеку

# Импортируем существующие модели и сериализаторы
from .models import (
    Tag, Ingredient, Recipe, AmountIngredient, Favorite, ShoppingCart
)
from users.serializers import CustomUserSerializer  # Для отображения автора


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Тег."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = fields  # Все поля только для чтения для этого API


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ингредиент."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields  # Все поля только для чтения для этого API



class TagInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов при создании/обновлении рецепта (ожидаем только ID)."""
    # Мы будем использовать PrimaryKeyRelatedField в RecipeWriteSerializer
    # Этот сериализатор может быть не нужен, если мы просто передаем список ID.
    # Но если бы мы хотели валидировать что-то еще в теге, он мог бы пригодиться.
    # Пока оставим для ясности, что теги идентифицируются по ID.
    class Meta:
        model = Tag
        fields = ('id',)


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте (с количеством)."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    # amount - уже есть в модели AmountIngredient

    class Meta:
        model = AmountIngredient  # Используем промежуточную модель
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения (отображения) рецептов.
    Соответствует схеме `RecipeList`.
    """
    tags = TagSerializer(many=True, read_only=True)
    # author = CustomUserSerializer(read_only=True)  # Используем сериализатор пользователя
    # ingredients = IngredientInRecipeReadSerializer(many=True, read_only=True, source='recipe_ingredients')
    # Заменил ingredients на SerializerMethodField для большей гибкости с source
    ingredients = serializers.SerializerMethodField(read_only=True)
    author = CustomUserSerializer(read_only=True)  # Для отображения автора как объекта

    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = fields  # Все поля только для чтения

    def get_ingredients(self, obj):
        """Получаем ингредиенты из промежуточной модели AmountIngredient."""
        amounts = AmountIngredient.objects.filter(recipe=obj)
        return IngredientInRecipeReadSerializer(amounts, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class IngredientAmountWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов при создании/обновлении рецепта.
    Ожидает id ингредиента и его количество.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=1
    )  # Валидация из модели AmountIngredient тоже сработает

    class Meta:
        model = AmountIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов.
    Соответствует схемам `RecipeCreate` и `RecipeUpdate`.
    """
    # image = serializers.ImageField(use_url=True)  # Стандартный ImageField не работает с base64
    image = Base64ImageField(required=True)  # Используем drf_extra_fields для base64
    ingredients = IngredientAmountWriteSerializer(
        many=True, allow_empty=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False  # Рецепт должен иметь хотя бы один тег
    )
    # author будет устанавливаться автоматически из request.user во view

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )
        # id и author не включаем, т.к. id генерируется, а author берется из запроса

    def validate_ingredients(self, ingredients_data):
        if not ingredients_data:
            raise serializers.ValidationError(
                "Список ингредиентов не может быть пустым."
            )
        ingredient_ids = [item['id'] for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты в рецепте не должны повторяться."
            )
        # Дополнительные валидации, если нужны (например, проверка существования ингредиентов,
        # хотя PrimaryKeyRelatedField это уже делает)
        return ingredients_data

    def validate_tags(self, tags_data):
        if not tags_data:
            raise serializers.ValidationError(
                "Список тегов не может быть пустым."
            )
        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError(
                "Теги в рецепте не должны повторяться."
            )
        return tags_data

    def _create_or_update_ingredients(self, recipe, ingredients_data):
        """Вспомогательный метод для создания/обновления ингредиентов рецепта."""
        # Удаляем старые ингредиенты рецепта, если это обновление
        # AmountIngredient.objects.filter(recipe=recipe).delete()  # Не нужно, если обновляем существующие
        # Лучше обновить существующие или удалить/создать только изменившиеся.
        # Но для простоты реализации (и если порядок не важен), можно удалить и создать заново.
        # Однако, более корректно будет управлять связями.

        # Сначала удалим все текущие ингредиенты для данного рецепта, если это обновление
        # (при создании recipe.recipe_ingredients.all() будет пуст)
        recipe.recipe_ingredients.all().delete()

        ingredient_amounts_to_create = []
        for ingredient_data in ingredients_data:
            ingredient_amounts_to_create.append(
                AmountIngredient(
                    recipe=recipe,
                    ingredient=ingredient_data['id'],  # ingredient_data['id'] это уже объект Ingredient
                    amount=ingredient_data['amount']
                )
            )
        AmountIngredient.objects.bulk_create(ingredient_amounts_to_create)

    @transaction.atomic  # Обернем в транзакцию для атомарности
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)  # Устанавливаем теги
        self._create_or_update_ingredients(
            recipe, ingredients_data
        )  # Создаем ингредиенты с количеством

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        # Обновляем основные поля экземпляра рецепта
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        if 'image' in validated_data:  # Обновляем изображение, если оно передано
            instance.image = validated_data.get('image', instance.image)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            self._create_or_update_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """При выводе после создания/обновления используем RecipeReadSerializer."""
        request = self.context.get('request')
        return RecipeReadSerializer(
            instance, context={'request': request}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    Укороченный сериализатор для рецепта.
    Используется при добавлении в избранное/список покупок (согласно схеме `RecipeMinified`).
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields
