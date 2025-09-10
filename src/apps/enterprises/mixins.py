from core.mixins import CommonWebMixin
from .models import Enterprise


class WebEnterpriseMixin(CommonWebMixin):
    model = Enterprise
