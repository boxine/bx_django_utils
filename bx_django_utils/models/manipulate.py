"""
    Utilities to manipulate objects in database via models:
    e.g.:
        create/update/delete model entries etc.
"""
import dataclasses
import warnings
from typing import Optional, Type

from django.core.exceptions import FieldDoesNotExist
from django.db import models


STORE_BEHAVIOR_IGNORE = "i"  # Ignore the value completely
STORE_BEHAVIOR_SET_IF_EMPTY = "e"  # Use the value only if we currently have no one.
STORE_BEHAVIOR_SKIP_EMPTY = "s"  # Don't store empty values (and maybe overwrite existing one)


class InvalidStoreBehavior(FieldDoesNotExist):
    """
    Exception used in create_or_update() if "store_behavior" contains not existing field names.
    """
    pass


def create(*, ModelClass, call_full_clean=True, save_kwargs=None, **values):
    """
    Create a new model instance with optional validate before create.
    """
    instance = ModelClass(**values)
    if call_full_clean:
        instance.full_clean(validate_unique=False)  # Don't create non-valid instances
    if save_kwargs is None:
        save_kwargs = {}
    instance.save(force_insert=True, **save_kwargs)
    return instance


@dataclasses.dataclass
class CreateOrUpdateResult:
    """
    Result object returned by create_or_update2() with all information about create/save a model.
    Contains:
        Model instance, that is created or updated.
        List of model field names that are: Updated / ignored / not overwritten
    """
    # Model instance object that was created or updated:
    instance: Type[models.Model] = None

    # If True: new instance was created else: existing was updated:
    created: bool = False

    # Fields that are updated (Empty list if model was created!):
    updated_fields: list = dataclasses.field(default_factory=list)

    # Field names that ignored by "STORE_BEHAVIOR_IGNORE":
    ignored_fields: list = dataclasses.field(default_factory=list)

    # Field names that are not overwritten (STORE_BEHAVIOR_SET_IF_EMPTY):
    not_overwritten_fields: list = dataclasses.field(default_factory=list)

    # Field names that are not filles with empty value (STORE_BEHAVIOR_SKIP_EMPTY):
    skip_empty_values: list = dataclasses.field(default_factory=list)


def create_or_update2(
    *,
    ModelClass: Type[models.Model],
    lookup: dict = None,
    call_full_clean: bool = True,
    store_behavior: Optional[dict] = None,
    save_kwargs: Optional[dict] = None,
    **values
) -> CreateOrUpdateResult:
    """
    Create a new model instance or update a existing one and returns CreateOrUpdateResult instance
    Similar to django's own create_or_update() but:

     * Use "update_fields" in save() call to store only changed fields.
     * return the information about changed field names.
     * validate before save.
     * Accept a optional "store_behavior"

     "store_behavior" is a dict with information about overwriting field values, e.g.:

         store_behavior = {
            'field_name1': STORE_BEHAVIOR_IGNORE,
            'field_name2': STORE_BEHAVIOR_SET_IF_EMPTY,
            'field_name3': STORE_BEHAVIOR_SKIP_EMPTY,
            ...
         }

     behaviors are:
      - STORE_BEHAVIOR_IGNORE........: Never store a given value to the model field
      - STORE_BEHAVIOR_SET_IF_EMPTY..: Store given value only if current field value is empty
      - STORE_BEHAVIOR_SKIP_EMPTY....: Don't store empty values to the field (protect existing)
    """
    if save_kwargs is None:
        save_kwargs = {}
    result = CreateOrUpdateResult()

    to_be_ignore_fields = set()  # Fields that should be ignored.
    to_be_set_if_empty_fields = set()  # Fields that should are set only when empty.
    to_be_skiped_if_empty = set()  # Fields that should not filled with empty values

    if store_behavior:
        opts = ModelClass._meta
        all_field_names = {
            # Note: We collect intentionally all fields + relations etc.
            # Maybe relations will be handled in external code parts ;)
            field.name
            for field in opts.get_fields(include_parents=True, include_hidden=True)
        }
        for field_name, behavior in store_behavior.items():
            if field_name not in all_field_names:
                raise InvalidStoreBehavior(
                    f'store_behavior field name {field_name!r}'
                    f' is not one of: {sorted(all_field_names)}'
                )

            if behavior == STORE_BEHAVIOR_IGNORE:
                # Values for this field should be completely ignored
                to_be_ignore_fields.add(field_name)
            elif behavior == STORE_BEHAVIOR_SET_IF_EMPTY:
                # Field values should be only stored, if existing field is empty
                to_be_set_if_empty_fields.add(field_name)
            elif behavior == STORE_BEHAVIOR_SKIP_EMPTY:
                # Fields that should not filled with empty values
                to_be_skiped_if_empty.add(field_name)
            else:
                raise KeyError(f'Unknown store behavior: {behavior!r} !')

    if not to_be_ignore_fields:
        filtered_values = values
    else:
        # Just filter every field values that we should ignore:
        filtered_values = {}
        for key, value in values.items():
            if key in to_be_ignore_fields:
                result.ignored_fields.append(key)
            else:
                filtered_values[key] = value

    if lookup is None:
        # Create a new object
        instance = create(
            ModelClass=ModelClass, call_full_clean=call_full_clean, save_kwargs=save_kwargs,
            **filtered_values)
        result.instance = instance
        result.created = True
        return result

    # Try to update a existing object
    assert isinstance(lookup, dict)
    instance = ModelClass.objects.filter(**lookup).first()
    if not instance:
        instance = create(
            ModelClass=ModelClass,
            call_full_clean=call_full_clean,
            save_kwargs=save_kwargs,
            **lookup,
            **filtered_values
        )
        result.instance = instance
        result.created = True
        return result

    # Store values:

    for field_name, value in filtered_values.items():
        if not value and field_name in to_be_skiped_if_empty:
            # We should not store empty value (and maybe overwrite existing one):
            result.skip_empty_values.append(field_name)
            continue

        old_value = getattr(instance, field_name)

        if old_value and field_name in to_be_set_if_empty_fields:
            # We should not overwrite this existing field value!
            result.not_overwritten_fields.append(field_name)
            continue

        if old_value != value:
            setattr(instance, field_name, value)
            result.updated_fields.append(field_name)

    if result.updated_fields:
        if call_full_clean:
            instance.full_clean(validate_unique=False)  # Don't save new non-valid values
        instance.save(update_fields=result.updated_fields, **save_kwargs)

    result.instance = instance

    return result


def create_or_update(
    *,
    ModelClass: Type[models.Model],
    lookup: dict = None,
    call_full_clean: bool = True,
    **values
):
    """
    Create a new model instance or update a existing one. Deprecated! Use: create_or_update2()
    """
    warnings.warn(
        'create_or_update() is deprecated, please use create_or_update2()',
        DeprecationWarning
    )
    result = create_or_update2(
        ModelClass=ModelClass, lookup=lookup, call_full_clean=call_full_clean, **values
    )
    instance = result.instance
    created = result.created
    updated_fields = result.updated_fields or None  # mimic old return value: None and not []
    return instance, created, updated_fields
