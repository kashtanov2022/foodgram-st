from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, status

from recipes.models import Recipe  # Для UserWithRecipes
from .models import Follow

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Сериализатор для создания пользователей.
    Переопределяем для соответствия схеме `CustomUserCreate`.
    """
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')
        # id будет read-only, password write-only по умолчанию в Djoser

    # Djoser уже обрабатывает создание пользователя и хеширование пароля,
    # так что здесь обычно не требуется переопределять create, если стандартное
    # поведение Djoser подходит. Поля соответствуют схеме.


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для отображения информации о пользователях.
    Добавляет поле is_subscribed.
    """
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar')  # Добавили avatar
        read_only_fields = ('email', 'id', 'username', 'first_name',
                            'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий аутентифицированный пользователь
        на пользователя `obj`.
        """
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(user=request.user, following=obj).exists()


class SubscribeRecipeMinifieldSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о рецептах в подписках."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(CustomUserSerializer):
    """
    Сериализатор для отображения пользователя с его рецептами (для подписок).
    Соответствует схеме `UserWithRecipes`.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes',
                                                      'recipes_count')
        read_only_fields = fields

    def get_recipes(self, obj):
        """
        Возвращает список рецептов пользователя `obj` с учетом параметра
        recipes_limit.
        """
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit') \
            if request else None
        recipes_queryset = obj.recipes.all()  # Получаем все рецепты автора obj

        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes_queryset = recipes_queryset[:recipes_limit]
            except ValueError:
                # Если recipes_limit невалидный, можно вернуть все или ничего,
                # или обработать как ошибку. Пока возвращаем все.
                pass
        serializer = SubscribeRecipeMinifieldSerializer(
            recipes_queryset, many=True, context={'request': request})
        return serializer.data


class FollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и отображения подписок.
    Используется UserWithRecipesSerializer для представления пользователя.
    """
    # Используем UserWithRecipesSerializer для отображения данных пользователя,
    # на которого подписываемся или который уже в подписках.
    # Но при создании подписки (POST) нам нужен только id пользователя.
    # Для этого можно использовать разные сериализаторы для чтения и записи,
    # или кастомизировать to_representation и to_internal_value.

    # Djoser для /users/{id}/subscribe/ ожидает, что мы вернем
    # информацию о пользователе, на которого подписались.
    # Мы можем переопределить ViewSet Djoser или создать свой.
    # Проще создать свой ViewSet для подписок.

    # Этот сериализатор будет использоваться для вывода списка подписок
    # внутри UserWithRecipesSerializer, который соответствует
    # CustomUserSerializer и добавляет рецепты.
    # Поля для этого сериализатора будут определяться
    # UserWithRecipesSerializer.

    # Если бы мы делали отдельный сериализатор для
    # /api/users/{id}/subscribe/ (POST):
    # following = serializers.PrimaryKeyRelatedField(
    #     queryset=User.objects.all())

    class Meta:
        model = Follow
        # Поля будут зависеть от контекста использования.
        # Djoser's subscribe endpoint вернет данные пользователя, на которого
        # подписались, используя UserSerializer (который мы настроим как
        # CustomUserSerializer).
        # Для списка /api/users/subscriptions/ мы используем
        # UserWithRecipesSerializer.
        fields = '__all__'  # Заглушка, т.к. логика подписок будет во Views

    def validate(self, data):
        # Валидация будет происходить во View, т.к. user (подписчик) берется
        # из request.user
        # following (автор) берется из URL.
        # Здесь можно добавить валидацию, если бы 'user' и 'following'
        # передавались в теле запроса.
        user = self.context['request'].user
        following_id = self.context['view'].kwargs.get('id')
        # или 'user_id' в зависимости от URL Djoser

        if not User.objects.filter(id=following_id).exists():
            # Это должно обрабатываться на уровне ViewSet (get_object_or_404)
            raise serializers.ValidationError(
                "Пользователь, на которого вы пытаетесь подписаться, "
                "не найден.")

        following = User.objects.get(id=following_id)

        if user == following:
            raise serializers.ValidationError(
                {"errors": "Вы не можете подписаться на самого себя."},
                code=status.HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(user=user, following=following).exists():
            raise serializers.ValidationError(
                {"errors": "Вы уже подписаны на этого пользователя."},
                code=status.HTTP_400_BAD_REQUEST)
        return data


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для установки аватара."""
    avatar = serializers.ImageField(required=True)  # Используем ImageField

    class Meta:
        model = User
        fields = ('avatar',)

    # Метод update будет вызван, когда мы передадим instance пользователя.
    # Djoser не имеет встроенного эндпоинта для аватара, мы его добавим сами.