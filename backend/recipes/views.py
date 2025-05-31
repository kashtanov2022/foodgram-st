from django.db.models import Exists, OuterRef
from django.http import HttpResponse  # Для скачивания списка покупок
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    Tag, Ingredient, Recipe, Favorite, ShoppingCart, AmountIngredient
)
from .serializers import (
    TagSerializer, IngredientSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, RecipeMinifiedSerializer
)
from .permissions import IsAuthorOrReadOnly  # Создадим этот permission
from .filters import RecipeFilter  # Создадим этот класс фильтрации


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра тегов.
    Предоставляет только действия list и retrieve.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]  # Теги доступны всем
    # Отключаем пагинацию для тегов, как указано в схеме
    # (не было count/next/previous)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра ингредиентов.
    Предоставляет только действия list и retrieve.
    Реализует поиск по имени.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]  # Ингредиенты доступны всем
    # Отключаем пагинацию для ингредиентов, как указано в схеме
    pagination_class = None

    # Настройка поиска
    # Для простого поиска по началу имени можно использовать SearchFilter.
    # filter_backends = [filters.SearchFilter]
    # ^ - поиск по началу строки, регистронезависимый по умолчанию
    # search_fields = ['^name']

    # Или, для большей гибкости и точного соответствия ТЗ
    # (поиск по частичному вхождению в начале названия),
    # можно создать кастомный фильтр или переопределить get_queryset.
    # "Поиск по частичному вхождению в начале названия ингредиента."
    # (openapi-schema.yml)
    # Django ORM's `istartswith` подходит для этого.

    def get_queryset(self):
        """
        Переопределяем для реализации поиска по параметру 'name'.
        Поиск регистронезависимый по началу названия ингредиента.
        """
        queryset = super().get_queryset()
        name_query = self.request.query_params.get('name')
        if name_query:
            queryset = queryset.filter(name__istartswith=name_query)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления рецептами.
    """
    queryset = Recipe.objects.all()
    # Определим в get_serializer_class
    # serializer_class = RecipeReadSerializer
    # По умолчанию, автор или только чтение
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RecipeFilter
    # Поля, по которым можно сортировать
    ordering_fields = ['pub_date', 'name']
    ordering = ['-pub_date']  # Сортировка по умолчанию

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        # Для ответа на эти действия
        if self.action in ['favorite', 'shopping_cart']:
            return RecipeMinifiedSerializer
        return RecipeReadSerializer  # Для list, retrieve

    def perform_create(self, serializer):
        """При создании рецепта устанавливаем автора
        из текущего пользователя."""
        serializer.save(author=self.request.user)

    # queryset для list с аннотациями is_favorited и is_in_shopping_cart
    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related(
            'tags', 'author', 'recipe_ingredients__ingredient'
        )
        user = self.request.user
        if user.is_authenticated:
            favorited_subquery = Favorite.objects.filter(
                user=user,
                recipe=OuterRef('pk')
            )
            shopping_cart_subquery = ShoppingCart.objects.filter(
                user=user,
                recipe=OuterRef('pk')
            )
            queryset = queryset.annotate(
                is_favorited_annotated=Exists(favorited_subquery),
                is_in_shopping_cart_annotated=Exists(shopping_cart_subquery)
            )
        return queryset

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            # RecipeMinifiedSerializer
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite_entry = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite_entry.exists():
                return Response(
                    {"errors": "Рецепта не было в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_entry.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет или удаляет рецепт из списка покупок."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            # RecipeMinifiedSerializer
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            cart_entry = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not cart_entry.exists():
                return Response(
                    {"errors": "Рецепта не было в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_entry.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивает список покупок в виде TXT файла."""
        user = request.user
        # Собираем все ингредиенты из рецептов в списке покупок пользователя
        ingredients_summary = {}
        # Получаем все объекты AmountIngredient
        # для рецептов в корзине пользователя
        items_in_cart = AmountIngredient.objects.filter(
            recipe__in_shopping_carts__user=user
        ).select_related('ingredient')

        for item in items_in_cart:
            name = item.ingredient.name
            unit = item.ingredient.measurement_unit
            amount = item.amount
            if (name, unit) in ingredients_summary:
                ingredients_summary[(name, unit)] += amount
            else:
                ingredients_summary[(name, unit)] = amount

        if not ingredients_summary:
            return Response(
                {"errors": "Ваш список покупок пуст."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Формируем текстовый файл
        content = "Список покупок Foodgram:\n\n"
        for (name, unit), total_amount in ingredients_summary.items():
            content += f"▢ {name.capitalize()} ({unit}) — {total_amount}\n"

        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
    
    @action(
        detail=True,
        methods=['get'],
        permission_classes=[permissions.AllowAny],
        url_path='get-link'
    )
    def copy_link(self, request, pk=None):
        recipe = self.get_object()
        
        frontend_path = f'/recipes/{recipe.id}/'
        
        full_frontend_url = request.build_absolute_uri(frontend_path)
        
        return Response(
            {'short-link': full_frontend_url},
            status=status.HTTP_200_OK
        )
