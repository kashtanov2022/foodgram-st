from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientSearchFilter, RecipeFilter
from .models import (Favorite, Ingredient, Recipe,
                     ShoppingCart, Tag)
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeSerializer, TagSerializer)
from users.serializers import RecipeMinifiedSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None 


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ('create',):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_or_remove_relation(self, request, pk, model):
        """Вспомогательный метод для добавления/удаления связи с рецептом."""
        recipe = get_object_or_404(Recipe, pk=pk)
        relation_exists = model.objects.filter(user=request.user, recipe=recipe).exists()

        if request.method == 'POST':
            if relation_exists:
                return Response(
                    {'errors': 'Рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not relation_exists:
            return Response(
                {'errors': 'Рецепта нет в списке.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного."""
        return self._add_or_remove_relation(request, pk, Favorite)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет или удаляет рецепт из списка покупок."""
        return self._add_or_remove_relation(request, pk, ShoppingCart)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивает список покупок в виде текстового файла."""
        ingredients = Recipe.objects.filter(
            shopping_cart__user=request.user
        ).values(
            'ingredients__name', 'ingredients__measurement_unit'
        ).annotate(total_amount=Sum('recipe_ingredients__amount'))

        shopping_list = "Список покупок:\n\n"
        for item in ingredients:
            name = item['ingredients__name']
            unit = item['ingredients__measurement_unit']
            amount = item['total_amount']
            shopping_list += f"- {name} ({unit}) — {amount}\n"
        
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получает ссылку на текущий рецепт"""
        recipe = self.get_object()
        
        frontend_path = f'/recipes/{recipe.id}/'
        
        full_frontend_url = request.build_absolute_uri(frontend_path)
        
        return Response({'short-link': full_frontend_url}, status=status.HTTP_200_OK)
