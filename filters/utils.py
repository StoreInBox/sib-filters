from django.apps import apps

from . import models


def get_filter_models():
    return [model for model in apps.get_models() if issubclass(model, models.FilterMixin)]
