from core.mixins import CommonWebMixin
from .models import Vehicle, Brand


class WebVehicleMixin(CommonWebMixin):
    model = Vehicle


class WebBrandMixin(CommonWebMixin):
    model = Brand
