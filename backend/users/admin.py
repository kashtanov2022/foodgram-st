from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscription, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Конфигурация админ-панели для пользователей."""
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    list_filter = ('email', 'first_name')
    search_fields = ('username', 'email')
    ordering = ('username',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Конфигурация админ-панели для подписок."""
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
