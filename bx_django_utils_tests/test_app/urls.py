from django.urls import path

from bx_django_utils_tests.test_app.views.dynamic_view_menu import MenuView, dynamic_view_menu


app_name = 'test_app'


urlpatterns = [
    path('', MenuView.as_view(), name='index'),
] + dynamic_view_menu.get_urls()  # Add all Fixup views
