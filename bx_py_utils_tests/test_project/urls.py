import debug_toolbar
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('bx_py_utils_tests.test_app.urls')),

    path('__debug__/', include(debug_toolbar.urls)),
]
