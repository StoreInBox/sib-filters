from django.db.models import signals

from .models import FilterMixin


def update_filter_on_creation(sender, instance, created=False, **kwargs):
    if created and instance.is_auto_update:
        instance.update()


def update_filter_on_product_change(sender, instance, signal, **kwargs):
    product = instance
    # This method is quite long but it is the simplest and good enough for now
    for filter_model in FilterMixin.get_all_models():
        for f in filter_model.objects.all():
            if product in f.get_queryset():
                if signal == signals.pre_delete:
                    f.update(deleted_product=product)
                else:
                    f.update()


def create_default_filters_for_category(sender, instance, created=False, **kwargs):
    if not created:
        return

    category = instance
    default_filter_models = [model for model in FilterMixin.get_all_models() if model.is_default()]
    for filter_model in default_filter_models:
        if not filter_model.objects.filter(category=category).exists():
            filter_model.objects.create(category=category, **filter_model.get_default_creation_kwargs())


def create_filters_for_category_descendants(sender, instance, created=False, **kwargs):
    if not created:
        return

    category_filter = instance
    category = category_filter.category
    for descendant in category.get_descendants():
        if not sender.objects.filter(category=descendant).exists():
            sender.objects.create(
                category=descendant,
                name=category_filter.name,
                priority=category_filter.priority,
                is_auto_update=category_filter.is_auto_update
            )
