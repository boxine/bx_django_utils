# bx_django_utils - Admin Extra Views

Helper to integrate class based views to the Django admin as easy as possible.

The views looks like normal Apps/Models.


## example

Add a view to the admin, e.g. `admin_views.py`:

```python
from django.http import HttpResponse
from django.views.generic.base import View

from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta, PseudoApp
from bx_django_utils.admin_extra_views.registry import register_admin_view

pseudo_app = PseudoApp(meta=AdminExtraMeta(name='You Pseudo App'))

@register_admin_view(pseudo_app=pseudo_app)
class DemoView2(AdminExtraViewMixin, View):
    meta = AdminExtraMeta(name='Example View')

    def get(self, request):
        return HttpResponse('Hello World!')
```

**Important:** You view class must registered explicitly: Every view class must be imported on startup.
Our `auto discover` app ready hook will only find views in `admin_view` !
So store you views in e.g.: `.../your_app/admin_views.py` (or in a package named `admin_views`).

More examples here:

* https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils_tests/test_app/admin_views.py


### Access/visibility permissions

`AdminExtraMeta.conditions` contains functions that control access.
If nothing is specified, `only_staff_user()` is added.

`conditions` can be specified in `PseudoApp` and the view. All `PseudoApp` will be added to the view conditions.

e.g.:

```python
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta, PseudoApp


def only_john_can_access(request):
    if request.user.is_superuser:
        return True
    if request.user.username == 'john':
        return True
    else:
        return False


pseudo_app = PseudoApp(
    meta=AdminExtraMeta(name='You Pseudo App', conditions={only_john_can_access})
)
```


## setup


### urls.py

Use `extra_view_registry.get_urls()` to add the needed url patterns, e.g.:

```python
from django.contrib import admin
from django.urls import include, path

from bx_django_utils.admin_extra_views.registry import extra_view_registry


urlpatterns = [
    path('admin/', include(extra_view_registry.get_urls())),
    path('admin/', admin.site.urls),
    # ...
]
```


### settings.py

Add `admin_extra_views` to `INSTALLED_APPS`, e.g.:

```python
INSTALLED_APPS = [
    # ...
    'bx_django_utils.admin_extra_views.apps.AdminExtraViewsAppConfig',
    'bx_django_utils.admin_extra_views.admin_config.CustomAdminConfig', # Replaced 'django.contrib.admin'
    # ...
]
```

Note: `CustomAdminConfig` sets the default site to `ExtraViewAdminSite` and you have to remove `django.contrib.admin` from `INSTALLED_APPS`!

If you have a own `AdminConfig` then set `default_site` there. See: https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/admin_config.py


## tricks and tips

### redirect via urlpatterns

You can redirect in `urls.py` via `Redirect2AdminExtraView` to a admin extra view, e.g.:
```python
from bx_django_utils.admin_extra_views.views import Redirect2AdminExtraView

urlpatterns = [
    # ...
    path('old_url/', Redirect2AdminExtraView.as_view(admin_view=ExampleAdminExtraViewClass)),
    # ...
]
```

