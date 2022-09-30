from bx_django_utils.admin_utils.filters import NotAllSimpleListFilter


class NotAllSimpleListFilterDemo(NotAllSimpleListFilter):
    title = 'blank_field set'
    parameter_name = 'blank_field'

    def lookups(self, request, model_admin):
        return (
            ('all', 'All'),
            (None, 'Yes'),  # None -> default filter!
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'all':  # -> don't filter
            return queryset
        elif self.value() == 'no':  # -> Only without a "blank_field" value
            return queryset.filter(blank_field='')

        # Default -> Only items with a "blank_field" value
        return queryset.exclude(blank_field='')
