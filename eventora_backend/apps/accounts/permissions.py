"""
accounts/permissions.py
Custom DRF permission classes for role-based access control.
"""

from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    """Allows access only to users with the 'student' role."""
    message = 'Only students can perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)


class IsAdminUser(BasePermission):
    """Allows access only to users with the 'admin' role."""
    message = 'Only admins can perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin_user)


class IsAdminOrReadOnly(BasePermission):
    """Admins can do anything. Authenticated students can only read (GET)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_admin_user
