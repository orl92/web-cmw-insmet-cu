from apps.user_auth.views.login import LoginFormView, LogoutRedirectView
from apps.user_auth.views.profile import ProfileDetailView, ProfileUpdateView
from apps.user_auth.views.groups import GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView
from apps.user_auth.views.permission_profiles import (
    PermissionProfileListView, PermissionProfileCreateView,
    PermissionProfileUpdateView, PermissionProfileDeleteView,
)
from apps.user_auth.views.password import PasswordChangeView, AdminPasswordChangeView, UserPasswordResetView
from apps.user_auth.views.users import UserListView, UserCreateView, UserUpdateView, UserDeleteView, CustomerRegisterView
