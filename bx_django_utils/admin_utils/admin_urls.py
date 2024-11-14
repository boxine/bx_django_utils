"""
    Helpers to build Admin URLs
"""
from urllib.parse import urlencode

from django.contrib.admin.utils import quote
from django.db import models
from django.urls import reverse


ADMIN_LINK_TYPES = ('changelist', 'add', 'history', 'delete', 'change')


def admin_model_url(
    *,
    model_or_instance: models.Model | type[models.Model],
    action: str | None = None,  # Default is 'changelist' and 'change'
    admin_prefix: str = 'admin',
    current_app: str | None = None,
    params: dict | None = None,
):
    """
    Build Admin change, add, changelist, etc. links with optional filter parameters.

    'action' defaults to 'changelist' or 'change', depending on model or instance is given.
    """
    if action is None:
        if isinstance(model_or_instance, models.Model):
            action = 'change'
        else:
            action = 'changelist'

    assert (
        action in ADMIN_LINK_TYPES
    ), f'Action: {action!r} is not one of {", ".join(ADMIN_LINK_TYPES)}'

    opts = model_or_instance._meta
    app_label = opts.app_label
    model_name = opts.model_name

    if action in ('history', 'delete', 'change'):
        assert isinstance(
            model_or_instance, models.Model
        ), f'{model_or_instance!r} is no model instance!'
        pk = model_or_instance.pk
        args = (quote(pk),)
    else:
        args = None

    url = reverse(
        f'{admin_prefix}:{app_label}_{model_name}_{action}', current_app=current_app, args=args
    )

    if params:
        params = urlencode(params)
        url = f'{url}?{params}'

    return url


def admin_change_url(
    instance: models.Model,
    admin_prefix: str = 'admin',
    current_app: str | None = None,
    params: dict | None = None,
):
    """
    Shortcut to generate Django admin "change" url for a model instance.
    """
    assert isinstance(instance, models.Model), f'No model instance given: {instance}'
    return admin_model_url(
        model_or_instance=instance,
        action='change',
        admin_prefix=admin_prefix,
        current_app=current_app,
        params=params,
    )


def admin_history_url(
    instance: models.Model,
    admin_prefix: str = 'admin',
    current_app: str | None = None,
    params: dict | None = None,
):
    """
    Shortcut to generate Django admin "history" url for a model instance.
    """
    assert isinstance(instance, models.Model), f'No model instance given: {instance}'
    return admin_model_url(
        model_or_instance=instance,
        action='history',
        admin_prefix=admin_prefix,
        current_app=current_app,
        params=params,
    )


def admin_delete_url(
    instance: models.Model,
    admin_prefix: str = 'admin',
    current_app: str | None = None,
    params: dict | None = None,
):
    """
    Shortcut to generate Django admin "delete" url for a model instance.
    """
    assert isinstance(instance, models.Model), f'No model instance given: {instance}'
    return admin_model_url(
        model_or_instance=instance,
        action='delete',
        admin_prefix=admin_prefix,
        current_app=current_app,
        params=params,
    )


def admin_changelist_url(
    model_or_instance: models.Model | type[models.Model],
    admin_prefix: str = 'admin',
    current_app: str | None = None,
    params: dict | None = None,
):
    """
    Shortcut to generate Django admin "changelist" url for a model or instance.
    """
    return admin_model_url(
        model_or_instance=model_or_instance,
        action='changelist',
        admin_prefix=admin_prefix,
        current_app=current_app,
        params=params,
    )
