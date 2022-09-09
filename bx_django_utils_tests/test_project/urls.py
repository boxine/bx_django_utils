import debug_toolbar
from django.contrib import admin
from django.urls import include, path

from bx_django_utils.admin_extra_views.registry import extra_view_registry
from bx_django_utils.admin_extra_views.views import Redirect2AdminExtraView
from bx_django_utils_tests.test_app.admin_views import DemoView3


urlpatterns = [
    path('admin/', include(extra_view_registry.get_urls())),
    path('old_demo_3/', Redirect2AdminExtraView.as_view(admin_view=DemoView3)),
    path('admin/', admin.site.urls),
    path('', include('bx_django_utils_tests.test_app.urls')),
    path('__debug__/', include(debug_toolbar.urls)),
]
