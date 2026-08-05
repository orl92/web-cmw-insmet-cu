from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from apps.user_auth.forms.password import UserPasswordResetForm
from apps.user_auth.views import (
    AdminPasswordChangeView,
    CustomerRegisterView,
    GroupCreateView,
    GroupDeleteView,
    GroupListView,
    GroupUpdateView,
    LoginFormView,
    LogoutRedirectView,
    PasswordChangeView,
    PermissionProfileCreateView,
    PermissionProfileDeleteView,
    PermissionProfileListView,
    PermissionProfileUpdateView,
    ProfileDetailView,
    ProfileUpdateView,
    UserCreateView,
    UserDeleteView,
    UserListView,
    UserPasswordResetView,
    UserUpdateView,
)

app_name = 'user_auth'

urlpatterns = [
    # Login / Logout
    path('login/', LoginFormView.as_view(), name='login'),
    path('logout/', LogoutRedirectView.as_view(), name='logout'),
    # Grupos
    path('groups/', GroupListView.as_view(), name='groups_list'),
    path('group/create/', GroupCreateView.as_view(), name='group_create'),
    path('group/update/<uuid:uuid>/', GroupUpdateView.as_view(), name='group_update'),
    path('group/delete/<uuid:uuid>/', GroupDeleteView.as_view(), name='group_delete'),
    # Perfiles de permisos
    path(
        'permission_profiles/', PermissionProfileListView.as_view(), name='permission_profiles_list'
    ),
    path(
        'permission_profile/create/',
        PermissionProfileCreateView.as_view(),
        name='permission_profile_create',
    ),
    path(
        'permission_profile/update/<uuid:uuid>/',
        PermissionProfileUpdateView.as_view(),
        name='permission_profile_update',
    ),
    path(
        'permission_profile/delete/<uuid:uuid>/',
        PermissionProfileDeleteView.as_view(),
        name='permission_profile_delete',
    ),
    # Usuarios
    path('users/', UserListView.as_view(), name='users_list'),
    path('user/create/', UserCreateView.as_view(), name='user_create'),
    path('user/update/<uuid:uuid>/', UserUpdateView.as_view(), name='user_update'),
    path('user/delete/<uuid:uuid>/', UserDeleteView.as_view(), name='user_delete'),
    # Registro Clientes
    path('register/customer/', CustomerRegisterView.as_view(), name='customer_register'),
    # Perfil
    path('profile/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    # Password
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    path(
        'password_change/<uuid:uuid>/',
        AdminPasswordChangeView.as_view(),
        name='admin_password_change',
    ),
    path(
        'password_reset/',
        UserPasswordResetView.as_view(
            template_name='pages/user_auth/password/reset.html',
            form_class=UserPasswordResetForm,
        ),
        name='password_reset',
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='pages/user_auth/password/reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='pages/user_auth/password/reset_confirm.html',
            success_url=reverse_lazy('user_auth:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='pages/user_auth/password/reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
