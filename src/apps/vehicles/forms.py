from django import forms
from django.forms import ModelForm
from .models import Vehicle


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
