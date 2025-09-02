import inspect
from urllib.parse import quote_plus, unquote_plus

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count, QuerySet
from django.utils.translation import gettext_lazy as _


def register_list_filter(
    key: str,
    title: str,
    order: int = 0,  # Optional number to define the order of the filters
):
    """
    Decorator to register a filter method in a DecoratedSimpleListFilter.
    """
    def decorator(func):
        func._filter_key = key
        func._filter_title = title
        func._filter_order = order
        return func

    return decorator


class DecoratedSimpleListFilter(admin.SimpleListFilter):
    """
    Like SimpleListFilter but filters can be registered via register_list_filter() decorator.
    """

    def __init__(self, *args, **kwargs):
        self.lookups_data = []
        self.key2method = {}

        filter_methods = (
            method
            for name, method in inspect.getmembers(self, predicate=inspect.ismethod)
            if hasattr(method, '_filter_key')
        )
        for method in sorted(
            filter_methods, key=lambda m: (m._filter_order, m._filter_key)
        ):
            key = method._filter_key
            assert key not in self.key2method, (
                f'Duplicate {key=} in {self.__class__.__name__}.{method.__name__}'
            )
            self.key2method[key] = method
            self.lookups_data.append((key, method._filter_title))

        self.lookups_data = tuple(self.lookups_data)
        super().__init__(*args, **kwargs)

    def lookups(self, request, model_admin):
        return self.lookups_data

    def queryset(self, request, queryset: QuerySet) -> QuerySet | None:
        value = self.value()
        if method := self.key2method.get(value):
            return method(queryset)


class YesNoListFilter(DecoratedSimpleListFilter):
    """
    Quick way to create a Yes/No change list filter.
    """
    def filter_yes(self, queryset):
        raise NotImplementedError

    def filter_no(self, queryset):
        raise NotImplementedError

    @register_list_filter('1', _('Yes'), order=1)
    def _filter_yes(self, queryset):
        return self.filter_yes(queryset)

    @register_list_filter('0', _('No'), order=2)
    def _filter_no(self, queryset):
        return self.filter_no(queryset)


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
