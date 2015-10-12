from django.apps import apps
from django.conf import settings

from .exceptions import FilterSettingsError


class ExternalModels(object):
    PRODUCT_MODEL_KEY = 'Product'
    CATEGORY_MODEL_KEY = 'Category'
    CHARACTERISTIC_MODEL_KEY = 'Characteristic'

    EXTERNAL_MODELS_MAP = {
        'Product': PRODUCT_MODEL_KEY,
        'Category': CATEGORY_MODEL_KEY,
        'Characteristic': CHARACTERISTIC_MODEL_KEY,
    }

    def __getattr__(self, name):
        return self.get_model(name)

    def get_model(self, name):
        if not hasattr(self, name):
            path = self.get_model_path(name)
            try:
                model = apps.get_model(path)
            except LookupError as e:
                raise FilterSettingsError(
                    'Cannot import model "%s" for filters application: %s' % (name, e))
            setattr(self, name, model)
        return getattr(self, name)

    def get_model_path(self, name):
        if name not in self.EXTERNAL_MODELS_MAP:
            raise FilterSettingsError('Model %s is not defined as external model' % name)
        key = self.EXTERNAL_MODELS_MAP[name]
        try:
            filters_settings = settings.FILTERS
        except AttributeError:
            raise FilterSettingsError(
                'Cannot find FILTERS variable in settings. It need to be configured for application "filters"')
        try:
            path = filters_settings[key]
        except KeyError:
            raise FilterSettingsError(
                'Cannot find model "%s" in FILTERS settings. It has to be configured with key "%s"' % (name, key))
        return path


external_models = ExternalModels()
