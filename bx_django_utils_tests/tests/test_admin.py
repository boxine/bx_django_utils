from django.contrib.admin import ModelAdmin
from django.contrib.admin.sites import site as default_site
from django.test import TestCase


class GenericAdminTestCase(TestCase):
    def test_admin_tuple_fields(self):
        """
        All ModelAdmin class field names attributes are tuples. Because tuples are immutable.
        It's a bad idea change these attributes to a mutable list. This may cause side effects.
        Check here if every test ModelAdmin class has only tuples in these attributes.
        """
        # Collect all "tuple" attributes from base ModelAdmin class:
        tuple_attr_names = []
        for attr_name in dir(ModelAdmin):
            if attr_name.startswith('_'):
                continue

            value = getattr(ModelAdmin, attr_name)
            if isinstance(value, tuple):
                tuple_attr_names.append(attr_name)

        # Check samples:
        self.assertIn('list_display', tuple_attr_names)
        self.assertIn('readonly_fields', tuple_attr_names)

        self.assertGreaterEqual(len(tuple_attr_names), 10)

        checked_admins = []
        for model_admin in default_site._registry.values():
            admin_name = model_admin.__class__.__name__
            self.assertIsInstance(model_admin, ModelAdmin)

            for attr_name in tuple_attr_names:
                value = getattr(model_admin, attr_name)
                if value is not None:
                    self.assertIsInstance(value, tuple, msg=f'{admin_name=} {attr_name=}')

            checked_admins.append(admin_name)
        self.assertEqual(
            sorted(checked_admins),
            [
                'ApproveTestModelAdmin',
                'ColorFieldTestModelAdmin',
                'CreateOrUpdateTestModelAdmin',
                'GroupAdmin',
                'LogEntryAdmin',
                'TranslatedModelAdmin',
                'TranslatedSlugTestModelAdmin',
                'UserAdmin',
                'ValidateLengthTranslationsModelAdmin',
            ],
        )
