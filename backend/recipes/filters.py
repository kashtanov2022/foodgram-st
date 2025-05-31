import django_filters
from .models import Recipe, Tag
from users.models import User  # Для фильтрации по автору


class RecipeFilter(django_filters.FilterSet):
    """
    Фильтр для рецептов.
    Позволяет фильтровать по тегам (slug), автору (id),
    наличию в избранном (is_favorited) и списке покупок (is_in_shopping_cart).
    """
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False,  # Используем OR для тегов (любой из перечисленных)
        # Если нужно AND (все перечисленные), то conjoined=True
    )
    is_favorited = django_filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags']  # 'is_favorited' и 'is_in_shopping_cart' обрабатываются методами

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorited_by__user=user)
        # Если value is False или пользователь не аутентифицирован,
        # то не применяем этот фильтр активно (или можно отфильтровать те,
        # что НЕ в избранном)
        # Для простоты, если value=True и не аутентифицирован, вернет пустой
        # queryset, т.к. аноним не может иметь избранного.
        # Если value=False, то фильтр ничего не делает (показывает все).
        # Если нужно явно показывать "не избранные", то:
        # elif not value and user.is_authenticated:
        #     return queryset.exclude(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(in_shopping_carts__user=user)
        return queryset
