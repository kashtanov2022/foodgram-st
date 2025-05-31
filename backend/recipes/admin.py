from django.contrib import admin
# Для аннотации количества добавлений в избранное
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Tag, Ingredient, Recipe, AmountIngredient, Favorite, ShoppingCart
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color_display')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Цвет')
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="background-color: {0}; padding: 2px 8px; '
                'border-radius: 3px;">{0}</span>',
                obj.color
            )
        return "-"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)  # Поиск по названию (уже было)
    list_filter = ('measurement_unit',)


class AmountIngredientInline(admin.TabularInline):
    model = AmountIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ['ingredient']  # Удобный поиск ингредиентов


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author_link', 'cooking_time',
        'get_favorites_count', 'pub_date_formatted'
    )
    search_fields = (
        'name', 'author__username', 'author__email', 'text'
    )  # Поиск по автору и названию
    list_filter = ('author', 'tags', 'pub_date')
    filter_horizontal = ('tags',)
    inlines = [AmountIngredientInline]
    readonly_fields = (
        'get_favorites_count_display',
    )  # Отображение на странице редактирования рецепта
    autocomplete_fields = ['author']  # Удобный поиск автора

    def get_queryset(self, request):
        # Аннотируем количество добавлений в избранное для отображения в списке
        queryset = super().get_queryset(request).annotate(
            favorites_count_annotation=Count('favorited_by')
        )
        return queryset

    @admin.display(description='Автор', ordering='author__username')
    def author_link(self, obj):
        link = reverse("admin:users_user_change", args=[obj.author.id])
        return format_html(
            '<a href="{}">{}</a>', link, obj.author.username
        )

    @admin.display(
        description='В избранном (кол-во)',
        ordering='favorites_count_annotation'
    )
    def get_favorites_count(self, obj):
        # Используем аннотированное значение
        return obj.favorites_count_annotation

    @admin.display(description='В избранном (на странице рецепта)')
    def get_favorites_count_display(self, obj):
        # Это поле будет использоваться в readonly_fields
        # на странице редактирования
        return Favorite.objects.filter(recipe=obj).count()

    get_favorites_count_display.short_description = (
        'Количество добавлений в избранное'
    )

    @admin.display(description='Дата публикации', ordering='pub_date')
    def pub_date_formatted(self, obj):
        return obj.pub_date.strftime('%d.%m.%Y %H:%M')


@admin.register(AmountIngredient)
class AmountIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe_link', 'ingredient_link', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)
    autocomplete_fields = ['recipe', 'ingredient']

    @admin.display(description='Рецепт', ordering='recipe__name')
    def recipe_link(self, obj):
        link = reverse("admin:recipes_recipe_change", args=[obj.recipe.id])
        return format_html('<a href="{}">{}</a>', link, obj.recipe.name)

    @admin.display(description='Ингредиент', ordering='ingredient__name')
    def ingredient_link(self, obj):
        link = reverse(
            "admin:recipes_ingredient_change", args=[obj.ingredient.id]
        )
        return format_html('<a href="{}">{}</a>', link, obj.ingredient.name)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link', 'recipe_link', 'added_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added_at',)
    autocomplete_fields = ['user', 'recipe']

    @admin.display(description='Пользователь')
    def user_link(self, obj):
        link = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)

    @admin.display(description='Рецепт')
    def recipe_link(self, obj):
        link = reverse("admin:recipes_recipe_change", args=[obj.recipe.id])
        return format_html('<a href="{}">{}</a>', link, obj.recipe.name)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link', 'recipe_link', 'added_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added_at',)
    autocomplete_fields = ['user', 'recipe']

    @admin.display(description='Пользователь')
    def user_link(self, obj):
        link = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)

    @admin.display(description='Рецепт')
    def recipe_link(self, obj):
        link = reverse("admin:recipes_recipe_change", args=[obj.recipe.id])
        return format_html('<a href="{}">{}</a>', link, obj.recipe.name)
