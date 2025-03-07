from django.contrib.auth import views as auth_views
from django.urls import path

from accounts.forms.password.forms import UserPasswordResetForm
from accounts.views.group.views import (GroupCreateView, GroupDeleteView,
                                        GroupListView, GroupUpdateView)
from accounts.views.password.views import (AdminPasswordChangeView,
                                           PasswordChangeView)
from accounts.views.profile.views import ProfileDetailView, ProfileUpdateView
from accounts.views.user.views import (UserCreateView, UserDeleteView,
                                       UserListView, UserUpdateView)

urlpatterns = [
    # Grupos
    path('groups/', GroupListView.as_view(), name='groups'),
    path('group/create/', GroupCreateView.as_view(), name='create_group'),
    path('group/update/<uuid:uuid>/', GroupUpdateView.as_view(), name='update_group'),
    path('group/delete/<uuid:uuid>', GroupDeleteView.as_view(), name='delete_group'),
    # Usuarios
    path('users/', UserListView.as_view(), name='users'),
    path('user/create/', UserCreateView.as_view(), name='create_user'),
    path('user/update/<uuid:uuid>/', UserUpdateView.as_view(), name='update_user'),
    path('user/delete/<uuid:uuid>', UserDeleteView.as_view(), name='delete_user'),
    # Perfil
    path('user/profile/', ProfileDetailView.as_view(), name='profile'),
    path('user/profile/update/<uuid:uuid>/', ProfileUpdateView.as_view(), name='update_profile'),
    # Password
    path('user/password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('user/password_change/<uuid:uuid>/', AdminPasswordChangeView.as_view(), name='admin_password_change'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='pages/accounts/password/password_reset.html', form_class=UserPasswordResetForm), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='pages/accounts/password/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='pages/accounts/password/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='pages/accounts/password/password_reset_complete.html'), name='password_reset_complete'),
]