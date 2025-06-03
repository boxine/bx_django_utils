import hashlib
from contextlib import contextmanager
from uuid import UUID

from django.db import models
from django.db.models.base import ModelState
from django.db.models.options import Options
from django.db.models.signals import post_init


@contextmanager
def deterministic_primary_key(*ModelClasses, force_overwrite_pk: bool = True):
    """
    Context manager for unittests to use deterministic primary key for a model creation.
    """

    def post_init_handler(sender, instance, **kwargs):
        state: ModelState = instance._state
        adding: bool = state.adding
        if not adding:
            # Already saved in DB -> No need to set a new primary key
            return

        if pk := instance.pk:
            if not force_overwrite_pk:
                # A primary key is set to create this object and we should not overwrite it
                return

            # Check if object already exists in the database.
            # Otherwise, we would create a *new* object instead of updating the existing one!
            if sender.objects.filter(pk=pk).exists():
                # Already exists -> Nothing to do
                return

        next_index = sender.objects.count() + 1
        opts: Options = instance._meta
        pk_field = opts.pk
        if isinstance(pk_field, models.UUIDField):
            # Generate a deterministic prefix based on the model name
            hash_object = hashlib.sha256(opts.label.encode('utf-8'))
            prefix = hash_object.hexdigest()[:8]

            pk_value = UUID(f'{prefix}-0000-0000-0000-{next_index:012}')
            instance.pk = pk_value
        elif isinstance(pk_field, models.IntegerField):
            # Just use 10000 as "prefix". That works also for small integer fields.
            instance.pk = 10000 + next_index
        else:
            raise NotImplementedError(f'{sender=} {pk_field=}')

    for ModelClass in ModelClasses:
        post_init.connect(post_init_handler, sender=ModelClass)
    try:
        yield
    finally:
        for ModelClass in ModelClasses:
            post_init.disconnect(post_init_handler, sender=ModelClass)
