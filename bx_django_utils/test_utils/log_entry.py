
from django.contrib.admin.models import LogEntry


def get_django_log_entries(
    fields: tuple[str, ...] = ('content_type__model', 'object_repr', 'action_flag', 'change_message'),
    clear: bool = False,  # Remove all LogEntry for next test step?
):
    """
    Collect LogEntry data for tests.
    """
    data = list(LogEntry.objects.order_by('action_time').values_list(*fields))
    if clear:
        LogEntry.objects.all().delete()
    return data
