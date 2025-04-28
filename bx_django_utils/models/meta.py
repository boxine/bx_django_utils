from django.db import models


def get_field_choices(model: type[models.Model], field_names: tuple[str, ...]) -> list:
    """
    Build choices to select model fields. Use the verbose name of the field and handle related fields, too.
    >>> from django.contrib.auth.models import User
    >>> get_field_choices(User, ('username', 'is_staff', 'user_permissions__content_type'))
    [('username', 'username'), ('is_staff', 'staff status'), ('user_permissions__content_type', 'content type')]
    """
    choices = []
    for field_name in field_names:
        field = model._meta
        parts = field_name.split('__')  # Handle related fields
        for part in parts:
            field = field.get_field(part)
            if field.is_relation and hasattr(field, 'related_model'):
                field = field.related_model._meta
        choices.append((field_name, field.verbose_name))
    return choices
