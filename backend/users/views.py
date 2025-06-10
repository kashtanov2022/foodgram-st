from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Subscription, User
from .serializers import SubscriptionSerializer, AvatarSerializer


class CustomUserViewSet(UserViewSet):
    """ViewSet для работы с пользователями и подписками."""

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает авторов, на которых подписан пользователь."""
        authors = User.objects.filter(following__user=request.user)
        paginated_queryset = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписывает или отписывает пользователя от автора."""
        author = get_object_or_404(User, id=id)

        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Subscription.objects.filter(
                user=request.user, author=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=request.user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(
            user=request.user, author=author
        )
        if not subscription.exists():
            return Response(
                {'errors': 'Вы не были подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Добавляет или удаляет аватар пользователя."""
        user = self.request.user

        if request.method == 'PUT':
            if not request.data or 'avatar' not in request.data:
                return Response(
                    {'avatar': ['This field is required.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = AvatarSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        return super().get_object()

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        if self.action == 'retrieve':
            return [AllowAny()]
        return super().get_permissions()
