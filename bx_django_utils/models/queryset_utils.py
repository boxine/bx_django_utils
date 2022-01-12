from copy import deepcopy
from typing import Type

from django.db.models import Model, Q, QuerySet
from django.db.models.sql.where import NothingNode


def remove_filter(queryset: QuerySet, lookup: str) -> QuerySet:
    """
    Remove an applied .filter() from a QuerySet
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


def remove_model_filter(queryset: QuerySet, model: Type[Model]) -> QuerySet:
    """
    Remove an applied .filter() from a QuerySet if it contains references to the specified model
    """
    if queryset.query.is_empty():
        # Nothing to remove if queryset is empty e.g.: ...objects.none()
        return queryset

    queryset = deepcopy(queryset)  # remove the QuerySet's cache
    query = queryset.query

    def filter_lookups(node):
        if hasattr(node, 'lhs'):
            return node.lhs.target.model != model

        if isinstance(node, NothingNode):
            return False

        return len(list(filter(filter_lookups, node.children))) == len(node.children)

    query.where.children = list(filter(filter_lookups, query.where.children))

    return queryset
