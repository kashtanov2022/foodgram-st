from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Follow


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    # Если есть кастомные поля, которые нужно редактировать в админке,
    # их нужно добавить в fieldsets или add_fieldsets
    # Например, для аватара:
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('avatar',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('avatar',)}),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following', 'created_at')
    search_fields = ('user__username', 'following__username', 'user__email', 'following__email')
    list_filter = ('created_at',)


admin.site.register(User, UserAdmin)
