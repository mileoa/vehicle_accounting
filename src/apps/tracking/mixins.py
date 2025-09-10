from apps.tracking.models import Trip
from core.mixins import CommonWebMixin


class WebTripMixin(CommonWebMixin):
    model = Trip
