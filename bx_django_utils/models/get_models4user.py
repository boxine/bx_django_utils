from collections.abc import Iterable

from django import forms
from django.apps import AppConfig, apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.options import Options


def iter_user_models(user, permission_codename: str = 'view') -> Iterable[models.Model]:
    """
    Filter models for the given user.
    permission_codename e.g.: "view" | "add" | "change" | "delete" etc.
    """
    app_configs = apps.get_app_configs()
    for app_config in app_configs:
        models = app_config.get_models()
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__startswith=permission_codename,
            )
            if user.has_perms(permissions):
                yield model


def get_user_model_choices(user, permission_codename: str = 'view'):
    """
    Build a form choices list with all models the given user can "view" | "add" | "change" | "delete" etc.
    """
    choices = []
    for ModelClass in iter_user_models(user, permission_codename=permission_codename):
        options: Options = ModelClass._meta
        app_config: AppConfig = options.app_config

        verbose_name = f'{app_config.verbose_name} | {options.verbose_name}'
        choices.append((options.label, verbose_name))
    return choices


class SelectModelForm(forms.Form):
    """
    Form to select a model that the user can "view"
    """

    model_name = forms.ChoiceField(
        label='Model Name:',
        help_text='Only entries are visible to which you have read access.',
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)

        field = self.fields['model_name']
        field.choices = get_user_model_choices(user, permission_codename='view')
