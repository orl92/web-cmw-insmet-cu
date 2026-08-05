from apps.user_auth.views.groups import (
    GroupCreateView,
    GroupDeleteView,
    GroupListView,
    GroupUpdateView,
)
from apps.user_auth.views.login import LoginFormView, LogoutRedirectView
from apps.user_auth.views.password import (
    AdminPasswordChangeView,
    PasswordChangeView,
    UserPasswordResetView,
)
from apps.user_auth.views.permission_profiles import (
    PermissionProfileCreateView,
    PermissionProfileDeleteView,
    PermissionProfileListView,
    PermissionProfileUpdateView,
)
from apps.user_auth.views.profile import ProfileDetailView, ProfileUpdateView
from apps.user_auth.views.users import (
    CustomerRegisterView,
    UserCreateView,
    UserDeleteView,
    UserListView,
    UserUpdateView,
)

__all__ = [
    'GroupCreateView',
    'GroupDeleteView',
    'GroupListView',
    'GroupUpdateView',
    'LoginFormView',
    'LogoutRedirectView',
    'AdminPasswordChangeView',
    'PasswordChangeView',
    'UserPasswordResetView',
    'PermissionProfileCreateView',
    'PermissionProfileDeleteView',
    'PermissionProfileListView',
    'PermissionProfileUpdateView',
    'ProfileDetailView',
    'ProfileUpdateView',
    'CustomerRegisterView',
    'UserCreateView',
    'UserDeleteView',
    'UserListView',
    'UserUpdateView',
]
