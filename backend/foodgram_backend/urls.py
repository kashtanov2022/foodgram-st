"""
URL configuration for foodgram_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet # Импортируем наш ViewSet

# Создаем роутер и регистрируем наш ViewSet
# Djoser UserViewSet уже включает /users/ и /users/{id}/,
# а также /users/me/. Мы переопределяем его для добавления
# /users/{id}/subscribe/ и /users/subscriptions/ и /users/me/avatar
# Важно: Djoser должен регистрироваться *после* нашего ViewSet, если
# мы хотим переопределить его стандартные маршруты нашими, или мы должны
# убедиться, что наши URL-паттерны для подписок не конфликтуют.
# Проще всего зарегистрировать наш CustomUserViewSet, а Djoser's
# UserViewSet не использовать напрямую, а только его auth-эндпоинты.

# Давайте используем Djoser's UserViewSet для базовых операций (/users/, /users/{id}/, /users/me/)
# и расширим его нашими эндпоинтами для подписок.
# Djoser регистрирует UserViewSet по пути 'users'.

# Если CustomUserViewSet наследуется от DjoserUserViewSet, то Djoser
# автоматически подхватит его, если он зарегистрирован под 'users'.
# Или мы можем не регистрировать Djoser UserViewSet и зарегистрировать наш.

router_v1 = DefaultRouter()
router_v1.register(r'users', CustomUserViewSet, basename='users')
# router_v1.register(r'tags', ...) # Добавим позже для рецептов
# router_v1.register(r'ingredients', ...) # Добавим позже
# router_v1.register(r'recipes', ...) # Добавим позже

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router_v1.urls)), # Регистрируем наш роутер
    path('api/auth/', include('djoser.urls.authtoken')), # Эндпоинты для токенов Djoser

    # Если CustomUserViewSet не покрывает все нужные эндпоинты Djoser
    # (например, /activation/, /resend_activation/ и т.д., если они нужны),
    # то можно добавить djoser.urls, но исключить 'users':
    # path('api/', include('djoser.urls')), # Это зарегистрирует Djoser's UserViewSet под 'users'
                                          # что может конфликтовать, если мы хотим наш CustomUserViewSet.
]

# Убедимся, что djoser.urls не переопределяет наш CustomUserViewSet.
# Если CustomUserViewSet называется так же и наследуется, Djoser может его использовать.
# Проверим документацию Djoser по кастомизации UserViewSet.
# Djoser ищет UserViewSet по умолчанию. Если мы хотим наш, то лучше
# явно его зарегистрировать, а из djoser.urls взять только то, что не касается users.

# Уточненный подход для urls.py:
# Мы зарегистрировали наш CustomUserViewSet через router_v1.
# Он наследуется от DjoserUserViewSet, поэтому должен подхватить
# стандартные эндпоинты Djoser для пользователей (list, create, me, set_password и т.д.)
# плюс наши кастомные (subscribe, subscriptions, avatar).

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Для статики админки в DEBUG
