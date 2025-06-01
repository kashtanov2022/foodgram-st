from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Follow, User
from .serializers import (
    UserWithRecipesSerializer,
    UserAvatarSerializer
)


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
            return UserWithRecipesSerializer
        if self.action == 'avatar':
            return UserAvatarSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['avatar', 'subscribe', 'subscriptions']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        """
        Возвращает пользователей, на которых подписан текущий пользователь.
        """
        user = request.user
        followed_users = User.objects.filter(following__user=user)

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
        user_to_follow = self.get_object()
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
                user_to_follow, context={'request': request})
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

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='user-me-avatar'
    )
    def avatar(self, request):
        """Устанавливает или удаляет аватар для текущего пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Аватар не найден."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
