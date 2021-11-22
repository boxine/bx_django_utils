from copy import deepcopy

from django.db.models import Q, QuerySet
from django.db.models.sql.where import NothingNode


def remove_filter(queryset: QuerySet, lookup: str) -> QuerySet:
    """
    Remove a applied .filter() from a QuerySet
    """
    if queryset.query.is_empty():
        # Nothing to remove if queryset is empty e.g.: ...objects.none()
        return queryset

    queryset = deepcopy(queryset)  # remove the QuerySet's cache

    query = queryset.query

    clause, _ = query._add_q(Q(**{lookup: None}), query.used_aliases)

    def filter_lookups(node):
        if hasattr(node, 'lhs'):
            return node.lhs.target != clause.children[0].lhs.target

        if isinstance(node, NothingNode):
            return False

        return len(list(filter(filter_lookups, node.children))) == len(node.children)

    query.where.children = list(filter(filter_lookups, query.where.children))

    return queryset
