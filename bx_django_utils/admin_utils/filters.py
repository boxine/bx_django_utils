from urllib.parse import quote_plus, unquote_plus

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count


class NotAllSimpleListFilter(admin.SimpleListFilter):
    """
    Similar to SimpleListFilter, but don't add "All" choice.
    """

    def choices(self, changelist):
        """
        The origin SimpleListFilter.choices() inserts "All" as first choice.
        But we would like to have other filter as default.
        """
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }


class ExistingCountedListFilter(admin.SimpleListFilter):
    """
    Advanced SimpleListFilter that list only existing filter values with counts.
    """

    model_field_name = None  # Model field name to filter by
    value_fmt = '{value} ({count})'  # Used to generate the filter entry line

    def __init__(self, request, params, model, model_admin):
        if self.model_field_name is None:
            raise ImproperlyConfigured(
                f"List filter '{self.__class__.__name__}' does not specify a 'model_field_name'."
            )
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin: admin.ModelAdmin):
        qs = model_admin.get_queryset(request)
        qs = (
            qs.order_by(self.model_field_name)
            .values(self.model_field_name)
            .annotate(count=Count('pk'))
        )
        return [
            (
                quote_plus(filter_entry[self.model_field_name]),
                self.value_fmt.format(
                    value=filter_entry[self.model_field_name], count=filter_entry['count']
                ),
            )
            for filter_entry in qs
        ]

    def queryset(self, request, queryset):
        if filter_value := self.value():
            filter_value = unquote_plus(filter_value)
            filter_kwargs = {self.model_field_name: filter_value}
            return queryset.filter(**filter_kwargs)
