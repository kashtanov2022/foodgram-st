from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .models import Subscription, User
from recipes.models import Recipe
from recipes.fields import Base64ImageField


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки аватара."""
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        if not value:
            raise serializers.ValidationError('This field is required.')
        return value


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )


class CustomUserSerializer(UserSerializer):
    """Сериализатор для просмотра профиля пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на просматриваемого."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Урезанный сериализатор для рецептов в подписках."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор для отображения подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (
            CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes(self, obj):
        """Получает ограниченное количество рецептов автора."""
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                raise serializers.ValidationError(
                    {
                        'recipes_limit': 'Параметр recipes_limit должен быть целым числом.'
                    }
                )
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Считает общее количество рецептов у автора."""
        return obj.recipes.count()
