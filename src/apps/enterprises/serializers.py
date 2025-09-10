from .models import Enterprise
from rest_framework import serializers


class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = "__all__"
