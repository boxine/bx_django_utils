"""
    DEMO for bx_django_utils.view_utils.dynamic_menu_urls.DynamicViewMenu

    This DEMO menu is registeres in urls.py as root page.
    So see and use it, start dev. server and go to index page:

        bx_django_utils$ make start-dev-server
"""
from django.urls import reverse
from django.views.generic import RedirectView, TemplateView

from bx_django_utils.view_utils.dynamic_menu_urls import DynamicViewMenu


dynamic_view_menu = DynamicViewMenu()  # Init new menu instance


class MenuView(TemplateView):
    template_name = 'dynamic_view_menu/index.html'
    title = 'Dynamic View Menu - Index'

    def get_context_data(self):
        context = {
            'title': self.title,
            'menu': dynamic_view_menu.menu,
        }
        return super().get_context_data(**context)


class Redirect2AdminView(RedirectView):
    title = 'Go to Django Admin'

    def get_redirect_url(self, *args, **kwargs):
        return reverse('admin:index')


class DemoView1(TemplateView):
    template_name = 'dynamic_view_menu/demo.html'
    title = 'Dynamic View Menu - DEMO 1'

    def get_context_data(self):
        context = {
            'title': self.title,
            'content': 'DEMO 1 content',
        }
        return super().get_context_data(**context)


class DemoView2(TemplateView):
    template_name = 'dynamic_view_menu/demo.html'
    title = 'Dynamic View Menu - DEMO 2'

    def get_context_data(self):
        context = {
            'title': self.title,
            'content': 'DEMO 2 content',
        }
        return super().get_context_data(**context)


class DemoView3(TemplateView):
    template_name = 'dynamic_view_menu/demo.html'
    title = 'Dynamic View Menu - DEMO 3'

    def get_context_data(self):
        context = {
            'title': self.title,
            'content': 'DEMO 3 content',
        }
        return super().get_context_data(**context)


# Add views to menu and urls:
dynamic_view_menu.add_views(
    app_name='test_app',  # same as: test_app.urls.app_name !
    menu=(
        ('Section 1', {
            'views': (
                # (<ViewClass>, <url-name>)
                (Redirect2AdminView, 'redirect2admin'),  # url name -> 'test_app:redirect2admin'
            )
        }),
        ('Section 2', {
            'views': (
                (DemoView1, 'demo1'),
                (DemoView2, 'demo2'),
            )
        }),
        ('Section 3', {
            'views': (
                (DemoView3, 'demo3'),
            )
        }),
    )
)
