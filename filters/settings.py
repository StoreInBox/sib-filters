import sys

from django.apps import apps
from django.conf import settings

from .exceptions import FilterSettingsError


def init_external_models():
    PRODUCT_MODEL_KEY = 'Product'
    CATEGORY_MODEL_KEY = 'Category'
    CHARACTERISTIC_MODEL_KEY = 'Characteristic'

    current_module = sys.modules[__name__]
    try:
        filters_settings = settings.FILTERS
    except AttributeError:
        raise FilterSettingsError(
            'Cannot find FILTERS variable in settings. It need to be configured for application "filters"')

    _init_external_model(current_module, filters_settings, 'Product', PRODUCT_MODEL_KEY)
    _init_external_model(current_module, filters_settings, 'Category', CATEGORY_MODEL_KEY)
    _init_external_model(current_module, filters_settings, 'Characteristic', CHARACTERISTIC_MODEL_KEY)


def _init_external_model(current_module, filters_settings, name, key):
    try:
        path = filters_settings[key]
    except KeyError:
        raise FilterSettingsError(
            'Cannot find model "%s" in FILTERS settings. It has to be configured with key "%s"' % (name, key))
    try:
        model = apps.get_model(path)
    except LookupError as e:
        raise FilterSettingsError(
            'Cannot import model "%s" for filters application: %s' % (name, e))
    setattr(current_module, name, model)
