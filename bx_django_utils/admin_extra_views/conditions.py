from django.contrib.auth.models import User


def only_staff_user(request):
    """
    Pass only active staff users. The default condition for all admin extra views.
    """
    user: User = request.user
    if not user.is_authenticated:
        return False
    if not user.is_active:
        return False
    if not user.is_staff:
        return False
    return True
