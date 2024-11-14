import dataclasses
from collections.abc import Callable

from django.contrib.admin import AdminSite
from django.contrib.admin.sites import site as default_site
from django.utils.text import slugify

from bx_django_utils.admin_extra_views.conditions import only_staff_user

_APP_LABELS = set()
_URL_NAMES = set()


@dataclasses.dataclass
class AdminExtraMeta:
    """
    Stores information for pseudo app and pseudo models.
    """

    name: str  # localized display name
    app_label: str = None  # Optional: Will be set from name, if not defined

    # must all be met to display. If not set: only_staff_user() will be added:
    conditions: set[Callable] = dataclasses.field(default_factory=set)

    # Set via set_url_info():
    url: str = None
    url_name: str = None

    def __post_init__(self):
        if not self.app_label:
            self.app_label = slugify(self.name)

        elif slugify(self.app_label) != self.app_label:
            raise AssertionError(f'App label is not a valid slug: {self.app_label!r}')

        if not self.conditions:
            # Add default condition if nothing set:
            self.conditions.add(only_staff_user)

    def __eq__(self, other):
        return self.app_label == other.app_label

    def __hash__(self):
        return hash(self.app_label)

    def setup_app(self, pseudo_app):
        # Build URL information with the given parent pseudo app:
        self.url_name = f'{pseudo_app.meta.app_label}_{self.app_label}'
        if self.url_name in _URL_NAMES:
            raise AssertionError(f'App label combination {self.url_name!r} is not unique!')
        _URL_NAMES.add(self.url_name)

        self.url = f'{pseudo_app.meta.app_label}/{self.app_label}/'

        # Add parent pseudo app conditions:
        self.conditions = self.conditions.union(pseudo_app.meta.conditions)


@dataclasses.dataclass
class PseudoApp:
    """
    Represents information about a Django App. Instance must be pass to @register_admin_view()
    """

    meta: AdminExtraMeta = None

    # Will be filled by @register_admin_view():
    views: list = dataclasses.field(default_factory=list)

    # The Django Admin site for this extra views (optional):
    admin_site: AdminSite = None

    def __post_init__(self):
        assert isinstance(self.meta, AdminExtraMeta)

        if self.meta.app_label in _APP_LABELS:
            raise AssertionError(
                f'PseudoApp must be have a unique label! Current label is: {self.meta.app_label!r}'
            )
        _APP_LABELS.add(self.meta.app_label)

        if not self.admin_site:
            self.admin_site = default_site

    def __eq__(self, other):
        return self.meta.app_label == other.meta.app_label

    def __hash__(self):
        return hash(self.meta.app_label)
