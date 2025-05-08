from django.contrib import admin
from .models import Tag, Ingredient, Recipe, AmountIngredient, Favorite, ShoppingCart


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)

class AmountIngredientInline(admin.TabularInline): # Или admin.StackedInline
    model = AmountIngredient
    extra = 1 # Количество пустых форм для добавления
    min_num = 1 # Минимальное количество ингредиентов в рецепте

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'pub_date')
    search_fields = ('name', 'author__username', 'text')
    list_filter = ('author', 'tags', 'pub_date')
    filter_horizontal = ('tags',) # Удобный интерфейс для ManyToMany с тегами
    inlines = [AmountIngredientInline] # Встроенная форма для ингредиентов

@admin.register(AmountIngredient)
class AmountIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added_at',)

@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added_at')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('added_at',)