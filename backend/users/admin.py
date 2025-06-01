from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административная конфигурация для модели User."""
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_active', 'get_recipes_count'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('first_name', 'last_name', 'email', 'avatar')}),
    )
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('avatar',)}),
    )

    @admin.display(description='Кол-во рецептов')
    def get_recipes_count(self, obj):
        return obj.recipes.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Административная конфигурация для модели Follow."""
    list_display = ('id', 'user_link', 'following_link', 'created_at')
    search_fields = ('user__username', 'following__username',
                     'user__email', 'following__email')
    list_filter = ('created_at',)
    autocomplete_fields = ['user', 'following']

    @admin.display(description='Подписчик')
    def user_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)

    @admin.display(description='Автор')
    def following_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:users_user_change", args=[obj.following.id])
        return format_html('<a href="{}">{}</a>', link, obj.following.username)
