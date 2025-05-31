from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

# Импортируем кастомную модель User из приложения users
# Убедитесь, что приложение users будет выше recipes в INSTALLED_APPS
# или используйте settings.AUTH_USER_MODEL
from users.models import User  # Или используйте get_user_model позже


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        'название тега',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        'цвет в HEX',
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message=('Введите корректный HEX-код цвета '
                         '(например, #RRGGBB или #RGB).')
            )
        ],
        help_text='Цвет в формате HEX (например, #49B64E)'
    )
    slug = models.SlugField(
        'слаг',
        max_length=200,
        unique=True,
        help_text='Уникальный идентификатор тега (например, "breakfast")'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        'название ингредиента',
        max_length=200
    )
    measurement_unit = models.CharField(
        'единица измерения',
        max_length=200
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique_ingredient_unit')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,  # Используем импортированную модель User
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        'название рецепта',
        max_length=200
    )
    image = models.ImageField(
        'изображение',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='AmountIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'время приготовления (в минутах)',
        validators=[MinValueValidator(1, message='Время приготовления должно быть не менее 1 минуты.')]
    )
    pub_date = models.DateTimeField(
        'дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class AmountIngredient(models.Model):
    """Модель для связи Recipe и Ingredient с указанием количества."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'количество',
        validators=[MinValueValidator(1, message='Количество должно быть не менее 1.')]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return (f'{self.ingredient.name} ({self.amount} '
                f'{self.ingredient.measurement_unit}) в "{self.recipe.name}"')


class Favorite(models.Model):
    """Модель для избранных рецептов пользователя."""
    user = models.ForeignKey(
        User,  # Используем импортированную модель User
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Избранный рецепт'
    )
    added_at = models.DateTimeField(
        'дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_favorite_recipe')
        ]
        ordering = ['-added_at']

    def __str__(self):
        return f'"{self.recipe.name}" в избранном у {self.user.username}'


class ShoppingCart(models.Model):
    """Модель для списка покупок пользователя."""
    user = models.ForeignKey(
        User,  # Используем импортированную модель User
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_carts',
        verbose_name='Рецепт в списке покупок'
    )
    added_at = models.DateTimeField(
        'дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_shopping_cart_recipe')
        ]
        ordering = ['-added_at']

    def __str__(self):
        return f'"{self.recipe.name}" в списке покупок у {self.user.username}'
