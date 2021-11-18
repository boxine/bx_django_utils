from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.db.models import Q
from django.test import TestCase

from bx_django_utils.models.queryset_utils import remove_filter


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
