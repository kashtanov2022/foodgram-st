from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет редактировать объект только его автору.
    Для остальных (включая анонимных) доступно только чтение.
    """

    def has_permission(self, request, view):
        # Разрешаем GET, HEAD, OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для остальных методов (POST, PUT, DELETE)
        # пользователь должен быть аутентифицирован
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD, OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для методов изменения (PUT, DELETE) проверяем,
        # является ли пользователь автором объекта
        # Предполагается, что у объекта `obj` есть поле `author`
        return obj.author == request.user
