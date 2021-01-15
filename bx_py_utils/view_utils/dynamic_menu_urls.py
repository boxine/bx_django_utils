from django.urls import path


class DynamicViewMenu:
    """
    Simple storage for store information about views/urls to build a menu.

    Howto use this see test view here:
        bx_py_utils_tests/test_app/views/dynamic_view_menu.py
    """

    def __init__(self):
        self.menu = None
        self.urlpatterns = None

    def add_views(self, app_name, menu):
        self.menu = []
        self.urlpatterns = []
        for head_line, section_data in menu:
            views = section_data['views']

            menu_entries = []
            for ViewClass, url_name in views:
                title = ViewClass.title
                assert title, f'No title in {ViewClass}'

                # Add to menu:
                menu_entries.append({
                    'title': title,
                    'url_name': f'{app_name}:{url_name}',
                })

                # Add to urls:
                pattern = path(f'{url_name}/', ViewClass.as_view(), name=url_name)
                self.urlpatterns.append(pattern)

            self.menu.append({
                'head_line': head_line,
                'entries': menu_entries,
            })

    def get_urls(self):
        assert self.menu is not None, 'add_views() not used!'
        assert self.urlpatterns, 'No views added?!?'
        return self.urlpatterns
