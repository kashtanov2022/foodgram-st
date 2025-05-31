from django_filters import rest_framework as filters
from .models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    # author = filters.ModelChoiceFilter(queryset=User.objects.all()) # If you filter by author ID

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart'] # Add author if you filter by it

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value: # If value is True
            # Using the Favorite model:
            return queryset.filter(favorited_by__user=user).distinct()
            # If you were using a ManyToManyField directly on Recipe model for favorites:
            # return queryset.filter(favorited_by_users=user).distinct() # Adjust field name
        elif user.is_authenticated and not value: # If value is False
            return queryset.exclude(favorited_by__user=user).distinct()
        return queryset # Or handle unauthenticated users differently if needed

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            # Using the ShoppingCart model:
            return queryset.filter(in_shopping_carts__user=user).distinct()
            # If you were using a ManyToManyField directly on Recipe model for cart:
            # return queryset.filter(in_shopping_cart_for_users=user).distinct() # Adjust field name
        elif user.is_authenticated and not value:
            return queryset.exclude(in_shopping_carts__user=user).distinct()
        return queryset
