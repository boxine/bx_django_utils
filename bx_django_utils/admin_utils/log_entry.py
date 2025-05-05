"""
Helper functions around Django's admin LogEntry model.
"""

import json

from django.contrib.admin.models import ACTION_FLAG_CHOICES, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet

ACTION_FLAG_DICT = dict(ACTION_FLAG_CHOICES)


def validate_action_flag(value):
    """
    Validate that the action flag is one of the allowed values.
    """
    if value not in ACTION_FLAG_DICT:
        raise ValidationError(f'Action flag {value!r} is not one of {sorted(ACTION_FLAG_DICT.keys())}')


def create_log_entry(
    *,
    user,
    instance: models.Model,
    action_flag,
    change_message: str | list,
) -> LogEntry:
    """
    Helper to create `LogEntry` entries for a model instance.
    Note: `call_full_clean` will result in additional database queries.
    """
    content_type = ContentType.objects.get_for_model(instance)
    log_entry = LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=content_type.pk,
        object_id=instance.pk,
        object_repr=str(instance),
        action_flag=action_flag,
        change_message=change_message,
    )
    log_entry.full_clean()
    return log_entry


def get_change_message_strings(queryset: QuerySet | None = None) -> list[str]:
    """
    Get `LogEntry` change messages as plain strings build by `LogEntry.get_change_message()`.
    """
    if queryset is None:
        queryset = LogEntry.objects.order_by('action_time')
    queryset = queryset.only('change_message')
    result = [log_entry.get_change_message() for log_entry in queryset]
    return result


def get_log_message_data(queryset: QuerySet | None = None) -> list:
    """
    Get `LogEntry` change messages data structure as list.
    """
    if queryset is None:
        queryset = LogEntry.objects.order_by('action_time').all()
    log_messages = []
    for log_entry in queryset:
        if change_message := log_entry.change_message:
            try:
                change_message = json.loads(change_message)
            except json.JSONDecodeError:
                # Add the raw change message if it can't be decoded
                log_messages.append(str(log_entry))
            else:
                log_messages.extend(change_message)

    return log_messages


def get_log_entry_qs(
    *,
    model: models.Model | type[models.Model] | None = None,
    object_id: str | None = None,
    action_flag: int | None = None,
    order_by: str | None = 'action_time',
) -> QuerySet:
    """
    Get a QuerySet of LogEntry objects, with optional filtering by model, object ID, and action flag.
    """
    qs = LogEntry.objects.all().order_by(order_by)

    if model is not None:
        content_type = ContentType.objects.get_for_model(model)
        qs = qs.filter(content_type=content_type)

    if object_id is not None:
        qs = qs.filter(object_id=object_id)

    if action_flag is not None:
        validate_action_flag(action_flag)
        qs = qs.filter(action_flag=action_flag)

    return qs
