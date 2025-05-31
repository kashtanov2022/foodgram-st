from django.db import transaction
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from .models import (
    Tag, Ingredient, Recipe, AmountIngredient, Favorite, ShoppingCart
)
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Тег."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ингредиент."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте (с количеством)."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = AmountIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения (отображения) рецептов.
    """
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = fields

    def get_ingredients(self, obj: Recipe):
        amounts = obj.recipe_ingredients.all()
        return IngredientInRecipeReadSerializer(amounts, many=True, context=self.context).data # Pass context if needed by nested serializer

    def get_is_favorited(self, obj: Recipe):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if hasattr(obj, 'is_favorited_annotated'):
             return obj.is_favorited_annotated
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj: Recipe):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if hasattr(obj, 'is_in_shopping_cart_annotated'):
            return obj.is_in_shopping_cart_annotated
        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()


class IngredientAmountWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов при создании/обновлении рецепта.
    Ожидает id ингредиента и его количество.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        min_value=1,
        error_messages={
            'min_value': 'Количество должно быть не менее 1.',
            'invalid': 'Количество должно быть целым числом.'
        }
    )

    class Meta:
        model = AmountIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов.
    """
    image = Base64ImageField(required=True) # Image is still required
    ingredients = IngredientAmountWriteSerializer(
        many=True,
        allow_empty=False # At least one ingredient is required
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,      # <--- CHANGE 1: Make tags not strictly required for submission
        allow_empty=True,    # <--- CHANGE 2: Allow an empty list of tags if 'tags' key is provided
        # default=[]         # <--- CHANGE 3: (Optional but good practice) Provide a default empty list
    )
    # cooking_time is implicitly required by model. If you want to make it optional
    # on the serializer level and have a model default, you can add `required=False`
    # cooking_time = serializers.IntegerField(min_value=1, required=True) # Default, from model

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )

    def validate_ingredients(self, ingredients_data):
        if not ingredients_data: # This check is redundant if allow_empty=False is on the field
            raise serializers.ValidationError(
                "Список ингредиентов не может быть пустым."
            )
        ingredient_pks = []
        for item_data in ingredients_data:
            ingredient_instance = item_data.get('id')
            if not isinstance(ingredient_instance, Ingredient):
                raise serializers.ValidationError(
                    {"ingredients": "Обнаружен некорректный ID ингредиента."}
                )
            ingredient_pks.append(ingredient_instance.pk)
        if len(ingredient_pks) != len(set(ingredient_pks)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты в рецепте не должны повторяться."}
            )
        return ingredients_data

    def validate_tags(self, tags_data):
        # This validation is only called if 'tags' is present in the input data.
        # If 'tags' is not sent by the frontend, this method won't be called for tags.
        if tags_data: # Only validate if tags_data is not empty (it could be an empty list if allow_empty=True)
            tag_pks = [tag.pk for tag in tags_data]
            if len(tag_pks) != len(set(tag_pks)):
                raise serializers.ValidationError(
                    {"tags": "Теги в рецепте не должны повторяться."}
                )
        return tags_data # Return empty list or validated list

    def _set_ingredients(self, recipe, ingredients_data):
        AmountIngredient.objects.filter(recipe=recipe).delete()
        ingredient_amounts_to_create = []
        for ingredient_item in ingredients_data:
            ingredient_amounts_to_create.append(
                AmountIngredient(
                    recipe=recipe,
                    ingredient=ingredient_item['id'],
                    amount=ingredient_item['amount']
                )
            )
        if ingredient_amounts_to_create:
            AmountIngredient.objects.bulk_create(ingredient_amounts_to_create)

    @transaction.atomic
    def create(self, validated_data):
        # If 'tags' is not sent by frontend, and `required=False` + `default=[]` is used on the field,
        # validated_data['tags'] will be an empty list here.
        # If only `required=False` is used, and 'tags' is not sent, it won't be in validated_data.
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags', []) # Safely pop with a default empty list

        recipe = Recipe.objects.create(**validated_data) # author will be injected by view
        if tags_data: # Only set tags if they were provided and are not empty
            recipe.tags.set(tags_data)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None) # `None` indicates field wasn't in PATCH request

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        if 'image' in validated_data:
            instance.image = validated_data.get('image', instance.image)
        instance.save()

        if tags_data is not None: # If 'tags' was part of the request payload
            instance.tags.set(tags_data) # This will clear tags if tags_data is an empty list

        if ingredients_data is not None:
            self._set_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields