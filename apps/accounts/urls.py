from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from apps.accounts.forms.password.forms import UserPasswordResetForm
from apps.accounts.views.group.views import (
                                        GroupCreateView,
                                        GroupDeleteView,
                                        GroupListView,
                                        GroupUpdateView,
)
from apps.accounts.views.password.views import (
                                        AdminPasswordChangeView,
                                        PasswordChangeView,
                                        UserPasswordResetView,
)
from apps.accounts.views.profile.views import ProfileDetailView, ProfileUpdateView
from apps.accounts.views.user.views import (
                                        CustomerRegisterView,
                                        UserCreateView,
                                        UserDeleteView,
                                        UserListView,
                                        UserUpdateView,
)

app_name = 'accounts'

urlpatterns = [
    # Grupos
    path('groups/', GroupListView.as_view(), name='groups_list'),
    path('group/create/', GroupCreateView.as_view(), name='group_create'),
    path('group/update/<uuid:uuid>/', GroupUpdateView.as_view(), name='group_update'),
    path('group/delete/<uuid:uuid>/', GroupDeleteView.as_view(), name='group_delete'),
    # Usuarios
    path('users/', UserListView.as_view(), name='users_list'),
    path('user/create/', UserCreateView.as_view(), name='user_create'),
    path('user/update/<uuid:uuid>/', UserUpdateView.as_view(), name='user_update'),
    path('user/delete/<uuid:uuid>/', UserDeleteView.as_view(), name='user_delete'),
    # Registro Clientes
    path('register/customer/', CustomerRegisterView.as_view(), name='customer_register'),
    # Perfil
    path('user/profile/', ProfileDetailView.as_view(), name='profile_detail'),
    path('user/profile/update/<uuid:uuid>/', ProfileUpdateView.as_view(), name='profile_update'),
    # Password
    path('user/password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('user/password_change/<uuid:uuid>/', AdminPasswordChangeView.as_view(), name='admin_password_change'),
    path('password_reset/', UserPasswordResetView.as_view(template_name='pages/accounts/password/password_reset.html', form_class=UserPasswordResetForm), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='pages/accounts/password/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='pages/accounts/password/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete'),
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='pages/accounts/password/password_reset_complete.html'), name='password_reset_complete'),
]