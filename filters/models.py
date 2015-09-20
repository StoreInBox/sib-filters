from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _


# Filters looks too complex now need to add documentation and examples of usage


class FilterTypes(object):
    NUMERIC = 'numeric'
    CHOICES = 'choices'
    INTERVALS = 'intervals'


class FilterMixin(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=50)
    priority = models.FloatField(
        _('Priority'), default=1, help_text=_('Filters with higher priority are displayed higher on page'))
    is_auto_update = models.BooleanField(
        default=True,
        help_text=_('If auto update is activated - filter will be automatically fill his fields.'))

    # TODO: Add description for this methods
    def get_queryset(self):
        raise NotImplemented()

    def get_filter_query(self, field, **kwargs):
        raise NotImplemented()

    def get_type(self):
        raise NotImplemented()

    def base_update(self, field):
        raise NotImplemented()

    def update(self):
        raise NotImplemented()

    def get_item_prefix(self):
        return '{}-{}'.format(self.__class__.__name__.lower(), self.id)


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

    def get_filter_query(self, field, selected_min_value, selected_max_value):
        try:
            selected_min_value = float(selected_min_value)
            selected_max_value = float(selected_max_value)
        except ValueError:
            return models.Q()
        else:
            return models.Q(**{
                '{}__gte'.format(field): selected_min_value,
                '{}__lte'.format(field): selected_max_value})

    def base_update(self, field):
        max_and_min = self.get_queryset().aggregate(models.Max(field), models.Min(field))
        new_max_value = max_and_min['{}__max'.format(field)]
        new_min_value = max_and_min['{}__min'.format(field)]
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
        return [choice.strip() for choice in self.choices.split(',')]

    def get_filter_query(self, field, choices):
        return models.Q(**{'{}__in'.format(field): choices})

    def base_update(self, field):
        choices = set(self.get_queryset().values_list(field, flat=True))
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

    def get_filter_query(self, field, intervals):
        query = models.Q()
        for min_value, max_value in intervals:
            query |= models.Q(**{'{}__gte'.format(field): min_value, '{}__lte'.format(field): max_value})
        return query

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
