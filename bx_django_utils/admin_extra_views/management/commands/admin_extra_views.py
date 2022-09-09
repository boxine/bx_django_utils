from django.core.management.base import BaseCommand
from django.urls import reverse

from bx_django_utils.admin_extra_views.registry import extra_view_registry


class Command(BaseCommand):
    """
    Manage command "admin_extra_views": Info about registered admin extra views
    """

    help = 'Information about registered admin extra views'

    def handle(self, *args, **options):
        view_count = 0
        for pseudo_app in sorted(extra_view_registry.pseudo_apps, key=lambda x: x.meta.name):
            self.stdout.write('_' * 100)
            self.stdout.write(f'Pseudo app: {pseudo_app.meta.name!r}')
            for view_class in sorted(pseudo_app.views, key=lambda x: x.meta.name):
                view_count += 1
                self.stdout.write(f' * Pseudo model: {view_class.meta.name!r}')
                url = reverse(view_class.meta.url_name)
                self.stdout.write(f' * url: {url!r}')
                self.stdout.write('')

        self.stdout.write(f'\nThere exists: {view_count} admin extra views.')
