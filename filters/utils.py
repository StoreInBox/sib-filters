from django.db import models as django_models

from . import models


def get_filter_models():
    return [m for m in django_models.get_models() if isinstance(m, models.FilterMixin)]
