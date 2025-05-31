from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Follow

# Unregister the default User admin if it was registered by djoser or
# elsewhere without our custom admin
# This might not be necessary if djoser doesn't auto-register a UserAdmin
# when AUTH_USER_MODEL is custom.
# try:
#     admin.site.unregister(User)
# except admin.sites.NotRegistered:
#     pass


@admin.register(User)  # Используем декоратор для регистрации
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_active', 'get_recipes_count'  # Добавим количество
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    # Поля для редактирования (fieldsets) наследуются из BaseUserAdmin
    # Добавляем наше кастомное поле avatar, если оно еще не там
    # BaseUserAdmin.fieldsets уже включает основные поля.
    # Мы добавляли avatar в Фазе 1, убедимся, что это корректно.
    # Если first_name и last_name важны для отображения сразу при создании:
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
    list_display = ('id', 'user_link', 'following_link', 'created_at')
    search_fields = ('user__username', 'following__username',
                     'user__email', 'following__email')
    list_filter = ('created_at',)
    autocomplete_fields = ['user', 'following']  # Удобный поиск при добавлении

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
