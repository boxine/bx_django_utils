from __future__ import annotations

import uuid

from bx_py_utils.test_utils.assertion import assert_equal
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission


def filter_permission_names(permissions):
    """
    Generate a Permission model query filtered by names, e.g.: ['<app_label>.<codename>', ...]
    """
    permission_pks = []
    for permission in permissions:
        assert '.' in permission, f'Wrong format: {permission!r}'
        app_label, codename = permission.split('.')
        try:
            permission_pk = Permission.objects.only('pk').get(
                codename=codename,
                content_type__app_label=app_label
            ).pk
        except Permission.DoesNotExist as err:
            raise Permission.DoesNotExist(f"{err}: '{app_label}.{codename}'")

        permission_pks.append(permission_pk)
    qs = Permission.objects.filter(pk__in=permission_pks)
    return qs


def assert_permissions(user, permissions):
    """
    Check user permissions.
    This compares all user permissions: From user group and user object.
    """
    all_user_permissions = set()
    for backend in auth.get_backends():
        if hasattr(backend, "get_all_permissions"):
            all_user_permissions.update(backend.get_all_permissions(user))

    expected_permissions = set(permissions)
    assert all_user_permissions == expected_permissions, (
        f"{tuple(sorted(all_user_permissions))!r}"
        ' is not'
        f" {tuple(sorted(expected_permissions))}!r"
    )


def make_test_user(
    username=None,
    email='test@test.tld',
    password='t',
    is_active=True,
    is_staff=True,
    is_superuser=False,
    permissions=None
):
    """
    Create a test user and set given permissions.

    :param permissions: Queryset or list of Permission instances
    :return: User instance
    """
    if username is None:
        # Generate a unique username for tests that will create more than one user
        username = f'test {uuid.uuid4()}'

    User = get_user_model()
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_active=is_active,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    if permissions is not None:
        for permission in permissions:
            assert isinstance(permission, Permission)
        user.user_permissions.set(permissions)
    user = User.objects.get(pk=user.pk)
    return user


def make_minimal_test_user(
    username=None,
    email='test@test.tld',
    password='t',
    is_staff=True,
    permissions=None
):
    """
    Create a test user and set given permissions.

    :param permissions: List of strings like: 'auth.import', 'app_label.codename', ...
    :return: User instance
    """
    if permissions is not None:
        # convert string list to queryset
        permissions = filter_permission_names(permissions)

    user = make_test_user(
        username=username,
        email=email,
        password=password,
        is_staff=is_staff,
        permissions=permissions
    )
    return user


def make_max_test_user(
    username=None,
    email='test@test.tld',
    password='t',
    is_staff=True,
    exclude_permissions=None
):
    """
    Create a test user with all permissions *except* the {exclude_permissions} ones.

    :param exclude_permissions: List of strings like: 'auth.import', 'app_label.codename', ...
    :return: User instance
    """
    permissions = Permission.objects.all()
    for permission in exclude_permissions:
        assert '.' in permission, f'Wrong format: {permission!r}'
        app_label, codename = permission.split('.')
        qs = Permission.objects.filter(
            codename=codename,
            content_type__app_label=app_label
        )
        assert qs.exists(), f'Not exists: {permission!r}'
        permissions = permissions.exclude(
            codename=codename,
            content_type__app_label=app_label
        )

    user = make_test_user(
        username=username,
        email=email,
        password=password,
        is_staff=is_staff,
        permissions=permissions
    )
    return user


def assert_user_properties(user, properties: dict, raw_password: str | None = None) -> None:
    """
    Check a user instance with all properties and password (optional)
    """
    User = get_user_model()
    if not isinstance(user, User):
        raise AssertionError(
            f'Given user object (type={type(user).__name__!r})'
            f' is not a {settings.AUTH_USER_MODEL!r} instance.'
        )

    current_props = {}
    for attr_name in properties.keys():
        if attr_name == 'permissions':
            current_props['permissions'] = sorted(user.get_all_permissions())
        else:
            current_props[attr_name] = getattr(user, attr_name)

    assert_equal(current_props, properties)

    if raw_password is not None:
        if not user.check_password(raw_password):
            raise AssertionError(f'Password {raw_password!r} is wrong!')
