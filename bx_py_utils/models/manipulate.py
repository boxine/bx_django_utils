"""
    Utilities to manipulate objects in database via models:
    e.g.:
        create/update/delete model entries etc.
"""


def create_or_update(*, ModelClass, lookup, call_full_clean=True, **values):
    """
    Create a new model instance or update a existing one
    Similar to django's own create_or_update() but:

     * Use update_fields and save only changed fields
     * return the information about changed field names.
     * validate before save
    """
    assert isinstance(lookup, dict)
    instance = ModelClass.objects.filter(**lookup).first()
    if not instance:
        instance = ModelClass(**lookup, **values)
        if call_full_clean:
            instance.full_clean(validate_unique=False)  # Don't create non-valid instances
        instance.save()
        return instance, True, None

    updated_fields = []
    for key, value in values.items():
        if getattr(instance, key) != value:
            setattr(instance, key, value)
            updated_fields.append(key)

    if updated_fields:
        if call_full_clean:
            instance.full_clean(validate_unique=False)  # Don't save new non-valid values
        instance.save(update_fields=updated_fields)

    return instance, False, updated_fields
