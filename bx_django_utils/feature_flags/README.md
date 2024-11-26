# bx_django_utils - Feature Flags

Store feature flags persistent into Django cache/database.

All flags will be stored to cache and database and only on cache miss fetched again from database.

There is optional a [Admin Extra Views](https://github.com/boxine/bx_django_utils/blob/master/bx_django_utils/admin_extra_views/README.md) base class to manage all flags in the admin.

## how to use

Change your `settings`, e.g.:
```python
INSTALLED_APPS = [
    # ...
    'bx_django_utils.feature_flags.apps.FeatureFlagsAppConfig',
    # ...
]
```


Define somewhere a flag, e.g.:

```python
from bx_django_utils.feature_flags.data_classes import FeatureFlag


foo_feature_flag = FeatureFlag(
    cache_key='foo',
    human_name='Foo',
    description='This is a feature flag',
    initial_enabled=True,
)
```


Use this flag somewhere, e.g.:

```python
from my_flags import foo_feature_flag

def my_view(request):
    if not foo_feature_flag.is_enabled:
        raise NotImplemented
    #...
```


To manage all feature flags in the admin: Register `ManageFeatureFlagsBaseView` admin extra view, e.g.:

```python
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta, PseudoApp
from bx_django_utils.admin_extra_views.registry import register_admin_view
from bx_django_utils.feature_flags.admin_views import ManageFeatureFlagsBaseView


def can_manage_feature_flags(request):
    if request.user.is_superuser:
        return True
    return False

manage_flags_app = PseudoApp(
    meta=AdminExtraMeta(
        name='Feature Flags',
        app_label='feature_flags',
        conditions={can_manage_feature_flags},
    )
)


@register_admin_view(pseudo_app=manage_flags_app)
class ManageFeatureFlagsAdminExtraView(ManageFeatureFlagsBaseView):
    pass
```

## Performance considerations

By default, each time the flags state is evaluated (e.g. when calling `foo_feature_flag.is_enabled()`), the flag state is fetched from the database. This may cause poor performance in hot code paths.
You can limit this evaluation to once per n seconds by passing the `cache_duration=timedelta(seconds=n)` argument to the `FeatureFlag` constructor.
