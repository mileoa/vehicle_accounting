from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission


class RoleRequiredException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED


class HasRoleOrSuper(BasePermission):

    def __init__(self, *required_roles):
        self.required_roles = required_roles

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        for role in self.required_roles:
            if not hasattr(request.user, role):
                raise RoleRequiredException()
        return True

    def __call__(self):
        return self
