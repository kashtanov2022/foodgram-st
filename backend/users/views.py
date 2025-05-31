from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Follow, User
from .serializers import (
    CustomUserSerializer,
    UserWithRecipesSerializer,
    SetAvatarSerializer
)
# Пагинатор будет использоваться из глобальных настроек DRF


class CustomUserViewSet(DjoserUserViewSet):
    """
    Кастомный ViewSet для пользователей, наследуется от Djoser.
    Переопределяем queryset и сериализаторы, добавляем эндпоинты
    для подписок и аватара.
    """
    queryset = User.objects.all()
    # Сериализаторы уже настроены в DJOSER settings (user, current_user)

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer  # Для списка подписок
        if self.action == 'set_avatar':
            return SetAvatarSerializer
        # Для остальных действий (list, retrieve, me) Djoser
        # будет использовать 'user' или 'current_user' из DJOSER['SERIALIZERS']
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['set_avatar', 'delete_avatar', 'subscribe',
                             'subscriptions']:
            self.permission_classes = [IsAuthenticated]
        # Для остальных (list, retrieve) используются permissions из
        # DJOSER['PERMISSIONS']
        # или 'rest_framework.permissions.IsAuthenticatedOrReadOnly'
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        """
        Возвращает пользователей, на которых подписан текущий пользователь.
        """
        user = request.user
        followed_users = User.objects.filter(
            following__user=user)  # Пользователи, на которых подписан user

        page = self.paginate_queryset(followed_users)
        if page is not None:
            serializer = self.get_serializer(page, many=True,
                                             context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(followed_users, many=True,
                                         context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, id=None):
        """
        Подписывает или отписывает текущего пользователя на/от пользователя
        с id.
        """
        user_to_follow = self.get_object()  # Используем get_object() из
        # DjoserUserViewSet, который берет юзера по id из URL
        current_user = request.user

        if current_user == user_to_follow:
            return Response(
                {"errors": "Вы не можете подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Follow.objects.filter(user=current_user,
                                     following=user_to_follow).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=current_user, following=user_to_follow)
            serializer = UserWithRecipesSerializer(
                user_to_follow, context={'request': request})  # Возвращаем
            # данные о пользователе, на которого подписались
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = Follow.objects.filter(user=current_user,
                                                 following=user_to_follow)
            if not subscription.exists():
                return Response(
                    {"errors": "Вы не были подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['put'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def set_avatar(self, request):
        """Устанавливает аватар для текущего пользователя."""
        user = request.user
        serializer = self.get_serializer(user, data=request.data,
                                         partial=True)  # partial=True, т.к.
        # обновляем только аватар
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Возвращаем сериализованный User с обновленным аватаром
        response_serializer = CustomUserSerializer(
            user, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)  # Удаляем файл и сохраняем модель
        return Response(status=status.HTTP_204_NO_CONTENT)
