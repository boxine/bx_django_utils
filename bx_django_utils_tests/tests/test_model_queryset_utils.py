from django.contrib.auth.models import Group, User
from django.core.exceptions import FieldError
from django.db.models import Q
from django.test import TestCase

from bx_django_utils.models.queryset_utils import remove_filter, remove_model_filter
from bx_django_utils_tests.test_app.models import TranslatedModel


class QuerySetUtilsTestCase(TestCase):
    def test_remove_filter_basic(self):
        User.objects.create(username='bar1')
        User.objects.create(username='bar2')
        User.objects.create(username='foo1')
        User.objects.create(username='foo2')

        queryset = User.objects.order_by('username').all()
        assert list(queryset.values_list('username', flat=True)) == [
            'bar1', 'bar2', 'foo1', 'foo2'
        ]

        queryset = queryset.filter(username='foo1')
        assert list(queryset.values_list('username', flat=True)) == ['foo1']

        old_id = id(queryset)
        queryset = remove_filter(queryset, lookup='username')
        assert list(queryset.values_list('username', flat=True)) == [
            'bar1', 'bar2', 'foo1', 'foo2'
        ]
        assert id(queryset) != old_id

        queryset = queryset.filter(username__startswith='bar')
        assert list(queryset.values_list('username', flat=True)) == ['bar1', 'bar2']
        queryset = remove_filter(queryset, lookup='username')
        assert list(queryset.values_list('username', flat=True)) == [
            'bar1', 'bar2', 'foo1', 'foo2'
        ]

        queryset = queryset.filter(Q(username='bar1') | Q(username='bar2'))
        assert list(queryset.values_list('username', flat=True)) == ['bar1', 'bar2']
        queryset = remove_filter(queryset, lookup='username')
        assert list(queryset.values_list('username', flat=True)) == [
            'bar1', 'bar2', 'foo1', 'foo2'
        ]

        # Existing model field, but not filtered -> no problem:
        remove_filter(queryset, lookup='email')

        # Try to remove a not existing model field -> error:
        with self.assertRaises(FieldError) as cm:
            remove_filter(queryset, lookup='doesnotexists')
        error_msg = cm.exception.args[0]
        assert error_msg.startswith(
            "Cannot resolve keyword 'doesnotexists' into field. Choices are: "
        )

        # Test with a "empty" queryset:
        empty_queryset1 = User.objects.none()
        assert empty_queryset1.count() == 0
        empty_queryset2 = remove_filter(empty_queryset1, lookup='username')
        assert empty_queryset2.count() == 0
        assert empty_queryset1 is empty_queryset2  # In this case we get the same object back

        # Test with a KeyExtract
        TranslatedModel.objects.create(translated={'de-de': 'Apfel', 'fr-fr': 'pomme'})
        TranslatedModel.objects.create(translated={'de-de': 'Banane', 'fr-fr': 'banane'})
        qs = TranslatedModel.objects.filter(**{'translated__de-de': 'Apfel'})
        self.assertEqual(list(qs.values_list('translated__fr-fr', flat=True)), ['pomme'])

        # Removing this filter should return everyhting
        removed_qs = remove_filter(qs, 'translated')
        self.assertEqual(
            list(removed_qs.order_by('translated__fr-fr').values_list('translated__fr-fr', flat=True)),
            ['banane', 'pomme'],
        )

    def test_remove_model_filter(self):
        admins = Group.objects.create(name='admins')
        customers = Group.objects.create(name='customers')
        User.objects.create(username='Beatrice').groups.add(admins)
        User.objects.create(username='Benedict').groups.add(customers)
        User.objects.create(username='Bob').groups.add(admins)
        User.objects.create(username='Jessica').groups.add(admins)
        User.objects.create(username='John').groups.add(customers)

        # Construct sample query
        queryset = (
            User.objects
            .filter(username__startswith='B')
            .filter(groups__name__in=['admins'])
            .order_by('username').all())
        got = list(queryset.values_list('username', flat=True))
        assert got == ['Beatrice', 'Bob']

        # Remove model-referencing filter
        old_id = id(queryset)
        queryset = remove_model_filter(queryset, Group)
        got = list(queryset.values_list('username', flat=True))
        assert got == ['Beatrice', 'Benedict', 'Bob']
        assert id(queryset) != old_id

        # Not filtering by the model in the first place is no problem
        simple_queryset = User.objects.filter(username__contains='e')
        simple_queryset = remove_model_filter(simple_queryset, Group)
        got = list(simple_queryset.values_list('username', flat=True))
        assert got == ['Beatrice', 'Benedict', 'Jessica']

        # Test with an empty queryset
        empty_queryset1 = User.objects.none()
        assert empty_queryset1.count() == 0
        empty_queryset2 = remove_model_filter(empty_queryset1, Group)
        assert empty_queryset2.count() == 0
        assert empty_queryset1 is empty_queryset2  # In this case we get the same object back

        # Test with a KeyExtract
        TranslatedModel.objects.create(translated={'de-de': 'Apfel', 'fr-fr': 'pomme'})
        TranslatedModel.objects.create(translated={'de-de': 'Banane', 'fr-fr': 'banane'})
        qs = TranslatedModel.objects.filter(**{'translated__de-de': 'Apfel'})
        qs = remove_model_filter(qs, Group)
        self.assertEqual(list(qs.values_list('translated__fr-fr', flat=True)), ['pomme'])

        # Removing this filter should return everyhting
        removed_qs = remove_model_filter(qs, TranslatedModel)
        self.assertEqual(
            list(removed_qs.order_by('translated__fr-fr').values_list('translated__fr-fr', flat=True)),
            ['banane', 'pomme'],
        )
