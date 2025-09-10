from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ProtectedErrorException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "Невозможно удалить объект, так как он используется другими объектами."
    )
    default_code = "protected_error"


def custom_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        exception = ProtectedErrorException()
        return exception_handler(exception, context)
    return exception_handler(exc, context)
