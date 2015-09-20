# coding: utf-8
from __future__ import unicode_literals

from django.apps import AppConfig
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

from . import utils, handlers


class FiltersConfig(AppConfig):
    name = 'filters'
    verbose_name = _('Filters')

    def ready(self):
        for model in utils.get_filter_models():
            signals.post_save.connect(
                handlers.auto_update_filter,
                sender=model,
                dispatch_uid='filters.handlers.auto_update_filter',
            )
