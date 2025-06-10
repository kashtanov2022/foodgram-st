from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from .models import Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтр для рецептов."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            if value == 1:
                return queryset.filter(favorites__user=self.request.user)
            elif value == 0:
                return queryset.exclude(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            if value == 1:
                return queryset.filter(shopping_cart__user=self.request.user)
            elif value == 0:
                return queryset.exclude(shopping_cart__user=self.request.user)
        return queryset


class IngredientSearchFilter(SearchFilter):
    """Фильтр для поиска ингредиентов по названию."""
    search_param = 'name'
