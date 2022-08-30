from importlib import import_module

from django.apps import apps
from django.utils.module_loading import module_has_submodule


MODULE_NAME = 'admin_views'


def autodiscover_admin_views():
    found_modules = []
    for app_config in apps.get_app_configs():
        if module_has_submodule(app_config.module, MODULE_NAME):
            module = import_module(f'{app_config.name}.{MODULE_NAME}')
            found_modules.append(module)
    return found_modules
