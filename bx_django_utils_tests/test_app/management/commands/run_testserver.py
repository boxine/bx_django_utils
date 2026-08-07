import os

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    """
    Expand django.contrib.staticfiles runserver
    """
    help = "Setup test project and run django developer server"

    def verbose_call(self, command, *args, **kwargs):
        self.stderr.write("_" * 79)
        self.stdout.write(f"Call {command!r} with: {args!r} {kwargs!r}")
        self.stdout.flush()
        call_command(command, *args, **kwargs)

    def handle(self, *args, **options):

        if "RUN_MAIN" not in os.environ:
            # RUN_MAIN added by auto reloader, see: django/utils/autoreload.py

            # Create migrations for our test app
            # But these migrations should never commit!
            # On changes: Just delete the SQLite file and start fresh ;)
            self.verbose_call("makemigrations")

            self.verbose_call("migrate")

            # django.contrib.staticfiles.management.commands.collectstatic.Command
            self.verbose_call("collectstatic", interactive=False, link=True)

            User = get_user_model()
            qs = User.objects.filter(is_active=True, is_superuser=True)
            if qs.count() == 0:
                auto_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
                if auto_password:
                    user = User.objects.create_superuser(username='admin', password=auto_password)
                    self.stdout.write(f'Superuser created: {user.username!r} / {auto_password!r}')
                else:
                    self.verbose_call("createsuperuser")

        addr = os.environ.get('DJANGO_RUNSERVER_ADDR', '127.0.0.1:8000')
        self.verbose_call("runserver", addr, use_threading=False, use_reloader=True, verbosity=2)
