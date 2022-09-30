from django.contrib import admin


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
