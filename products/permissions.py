from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """Allow access only to Django superusers."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
