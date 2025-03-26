from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import CustomUser, Vehicle, VehicleDriver


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )

    class Meta:
        model = CustomUser
        fields = ["username", "password"]


class VehicleForm(ModelForm):

    purchase_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(),
        label="Время покупки",
    )

    class Meta:
        model = Vehicle
        fields = [
            "car_number",
            "price",
            "year_of_manufacture",
            "mileage",
            "description",
            "brand",
            "enterprise",
            "purchase_datetime",
        ]
