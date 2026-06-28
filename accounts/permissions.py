from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanEditDictionary(BasePermission):
    """Allow access only to dictionary editors (or superusers).

    An *editor* (``role=editor``) is a content manager who works in the
    front-end dictionary-management panel. The Django superuser additionally
    has access to the technical Django admin. See ``User.can_edit_dictionary``.
    """

    message = "Требуются права редактора словаря."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.can_edit_dictionary)


class CanEditDictionaryOrReadOnly(BasePermission):
    """Read for everyone; write only for dictionary editors."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.can_edit_dictionary)
