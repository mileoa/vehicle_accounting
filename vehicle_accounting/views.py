from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from rest_framework import viewsets
from .models import Vehicle, Brand, Driver, Enterprise, VehicleDriver
from .serializers import (
    VehicleSerializer,
    BrandSerializer,
    DriverSerializer,
    EnterpriseSerializer,
    ActiveVehicleDriverSerializer,
)


# Create your views here.
class VehicleViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


class BrandViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class DriverViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer


class EnterpriseViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    queryset = Enterprise.objects.all()
    serializer_class = EnterpriseSerializer


class ActiveVehicleDriverViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    queryset = VehicleDriver.objects.filter(is_active=True)
    serializer_class = ActiveVehicleDriverSerializer
