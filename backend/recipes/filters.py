from django_filters import rest_framework as filters
from .models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтер для рецептов на главной, в избранном и в корзине."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        ]

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorited_by__user=user).distinct()
        elif user.is_authenticated and not value:
            return queryset.exclude(favorited_by__user=user).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(in_shopping_carts__user=user).distinct()
        elif user.is_authenticated and not value:
            return queryset.exclude(in_shopping_carts__user=user).distinct()
        return queryset
