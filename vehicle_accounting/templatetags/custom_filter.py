from django import template
from vehicle_accounting.services import get_address_from_coordinates

register = template.Library()


@register.filter
def get_address(point):
    if point is None:
        return None
    lng, lat = point.point.x, point.point.y
    return get_address_from_coordinates(lat, lng)["address"]
