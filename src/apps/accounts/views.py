from django.contrib.auth.views import LoginView

from .forms import CustomLoginForm


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = "accounts/registration/login.html"
    redirect_authenticated_user = (True,)
