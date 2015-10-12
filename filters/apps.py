# coding: utf-8
from __future__ import unicode_literals

from django.apps import AppConfig
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _


class FiltersConfig(AppConfig):
    name = 'filters'
    verbose_name = _('Filters')

    def ready(self):
        from . import models, handlers, settings

        for index, model in enumerate(models.FilterMixin.get_all_models()):
            signals.post_save.connect(
                handlers.update_filter_on_creation,
                sender=model,
                dispatch_uid='filters.handlers.update_filter_on_creation_{}_{}'.format(model.__name__, index),
            )

        signals.post_save.connect(
            handlers.update_filter_on_product_change,
            sender=settings.external_models.Product,
            dispatch_uid='filters.handlers.update_filter_on_product_save',
        )

        signals.post_delete.connect(
            handlers.update_filter_on_product_change,
            sender=settings.external_models.Product,
            dispatch_uid='filters.handlers.update_filter_on_product_delete',
        )

        signals.post_save.connect(
            handlers.create_default_filters_for_category,
            sender=settings.external_models.Category,
            dispatch_uid='filters.handlers.create_default_filters_for_category',
        )
