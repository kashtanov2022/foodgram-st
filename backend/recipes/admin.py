from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Конфигурация админ-панели для тегов."""
    list_display = ('id', 'name', 'slug', 'color')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Конфигурация админ-панели для ингредиентов."""
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    """
    Inline для отображения ингредиентов на странице редактирования рецепта.
    """
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Конфигурация админ-панели для рецептов."""
    list_display = ('id', 'name', 'author', 'get_favorite_count')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name', 'author__username')
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Конфигурация админ-панели для избранного."""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Конфигурация админ-панели для списка покупок."""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
