from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy


class CommonWebMixin(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin
):
    pass
