from __future__ import unicode_literals

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.lru_cache import lru_cache
from django.utils.translation import ugettext_lazy as _

from .settings import external_models


# Filters looks too complex now need to add documentation and examples of usage


class FilterTypes(object):
    NUMERIC = 'numeric'
    CHOICES = 'choices'
    INTERVALS = 'intervals'


class FilterMixin(models.Model):
    name = models.CharField(max_length=50)
    priority = models.FloatField(
        _('Priority'), default=1, help_text=_('Filters with higher priority are displayed higher on page'))
    is_auto_update = models.BooleanField(
        default=True,
        help_text=_('If auto update is activated - filter will be automatically fill his fields.'))
    # Cannot use related name because many different filters can be connected to category
    category = models.ForeignKey(external_models.get_model_path('Category'), related_name='+')

    class Meta:
        abstract = True

    @classmethod
    def is_default(cls):
        """ Default filter will be connected to each category """
        return False

    @classmethod
    def get_default_creation_kwargs(cls):
        raise NotImplementedError(
            'Method "get_default_creation_kwargs" has to be implemented for default category filters')

    @classmethod
    def get_category_filters(cls, category):
        """ All filters related to given category """
        filters = []
        for filter_model in cls.get_all_models():
            filters += list(filter_model.objects.filter(category=category))
        return sorted(filters, key=lambda x: x.priority, reverse=True)

    @classmethod
    @lru_cache(maxsize=1)
    def get_all_models(cls):
        return [model for model in apps.get_models() if issubclass(model, cls)]

    def get_template_name(self):
        return self.__class__.__name__.lower()

    def get_field(self):
        raise NotImplementedError()

    # Update-related methods:
    def get_queryset(self):
        """ Get all products that are related to this filter """
        # XXX: Fragile. Need to check for category method in settings or rewrite this method.
        return self.category.get_products()

    def base_update(self, queryset):
        """ Execute filter update based on products from queryset """
        raise NotImplementedError()

    def update(self, deleted_product=None):
        """ Main update method """
        queryset = self.get_queryset()
        if deleted_product is not None:
            queryset = queryset.exclude(pk=deleted_product.pk)
        self.base_update(queryset)
        self.save()

    # filtering
    def get_filter_query(self, **kwargs):
        """ Get filter query for concrete field """
        raise NotImplementedError()

    def get_filter_kwargs(self, request):
        """ Get kwargs for filter query from request """
        raise NotImplementedError()

    def is_active(self, request):
        """ Return true if there are some values related to filter in request """
        raise NotImplementedError()

    def filter(self, queryset, request):
        """ Filter queryset based on values from request """
        if self.is_active(request):
            kwargs = self.get_filter_kwargs(request)
            query = self.get_filter_query(**kwargs)
            return queryset.filter(query)
        return queryset

    # XXX: Other methods. Do I really need them?
    def get_type(self):
        raise NotImplementedError()


class NumericFilterMixin(FilterMixin):
    """
    Abstract numeric filter mixin
    """
    max_value = models.FloatField(_('Max'), default=0)
    min_value = models.FloatField(_('Min'), default=0)

    class Meta:
        abstract = True

    def clean(self):
        if self.min_value > self.max_value:
            raise ValidationError(_('Min has to be lower then max'))
        return super(NumericFilterMixin, self).clean()

    def get_type(self):
        return FilterTypes.NUMERIC

    def get_filter_query(self, selected_min_value=None, selected_max_value=None):
        field = self.get_field()
        query_kwargs = {}
        if selected_min_value is not None:
            try:
                selected_min_value = float(selected_min_value)
            except (ValueError, TypeError):
                pass
            else:
                query_kwargs['{}__gte'.format(field)] = selected_min_value

        if selected_max_value is not None:
            try:
                selected_max_value = float(selected_max_value)
            except (ValueError, TypeError):
                pass
            else:
                query_kwargs['{}__lte'.format(field)] = selected_max_value

        return models.Q(**query_kwargs)

    def base_update(self, queryset):
        field = self.get_field()
        max_and_min = queryset.aggregate(models.Max(field), models.Min(field))
        new_max_value = max_and_min['{}__max'.format(field)] or 0
        new_min_value = max_and_min['{}__min'.format(field)] or 0
        if self.min_value != new_min_value or self.max_value != new_max_value:
            self.min_value = new_min_value
            self.max_value = new_max_value
            self.save()


class ChoicesFilterMixin(FilterMixin):
    """
    Abstract choices filter mixin
    """
    choices = models.TextField(_('Choices'), blank=True, help_text=_('Comma-separated list of choices'))

    class Meta:
        abstract = True

    def get_type(self):
        return FilterTypes.CHOICES

    def get_formatted_choices(self):
        return sorted([choice.strip() for choice in self.choices.split(',')])

    def get_filter_query(self, choices):
        field = self.get_field()
        return models.Q(**{'{}__in'.format(field): choices})

    def base_update(self, queryset):
        field = self.get_field()
        choices = sorted(list(set(queryset.values_list(field, flat=True))))
        self.choices = ', '.join(choices)
        self.save()


class IntervalsFilterMixin(FilterMixin):
    """
    Abstract intervals filter mixin
    """
    intervals = models.TextField(
        _('Intervals'), blank=True, help_text=_('Comma-separated list of intervals. Example: 0-100, 100-200 ...'))

    class Meta:
        abstract = True

    def get_type(self):
        return FilterTypes.INTERVALS

    def get_formatted_intervals(self):
        intervals = [interval.strip() for interval in self.intervals.split(',')]
        return [(float(i.split('-')[0].strip()), float(i.split('-')[1].strip())) for i in intervals]

    def get_filter_query(self, intervals):
        field = self.get_field()
        query = models.Q()
        for min_value, max_value in intervals:
            query |= models.Q(**{'{}__gte'.format(field): min_value, '{}__lte'.format(field): max_value})
        return query

    def base_update(self, queryset):
        raise NotImplementedError('Intervals filter does not support auto update')

    def clean(self):
        if self.is_auto_update:
            self.is_auto_update = False
        if not self.intervals:
            raise ValidationError('Intervals have to be manually inserted for interval filter')
        try:
            self.get_formatted_intervals()
        except (IndexError, ValueError):
            raise ValidationError('Intervals are inputed in wrong format')
        return super(IntervalsFilterMixin, self).clean()


class ChoicesProductFieldFilterMixin(ChoicesFilterMixin):
    class Meta:
        abstract = True

    def is_active(self, request):
        return self.get_field() in request.GET

    def get_filter_kwargs(self, request):
        try:
            selected_indexes = [int(index) for index in request.GET.getlist(self.get_field())]
        except ValueError:
            selected_choices = []
        else:
            selected_choices = [choice for index, choice in enumerate(self.get_formatted_choices(), 1)
                                if index in selected_indexes]
        return {'choices': selected_choices}


class NumericProductFieldFilterMixin(NumericFilterMixin):
    class Meta:
        abstract = True

    MIN_SUFFIX = '_min'
    MAX_SUFFIX = '_max'

    def is_active(self, request):
        return self.get_field() + self.MIN_SUFFIX in request.GET or self.get_field() + self.MAX_SUFFIX in request.GET

    def get_filter_kwargs(self, request):
        kwargs = {}
        if self.get_field() + self.MIN_SUFFIX in request.GET:
            kwargs['selected_min_value'] = request.GET[self.get_field() + self.MIN_SUFFIX]
        if self.get_field() + self.MAX_SUFFIX in request.GET:
            kwargs['selected_max_value'] = request.GET[self.get_field() + self.MAX_SUFFIX]
        return kwargs


# TODO: Implement product characteristic filter mixin
