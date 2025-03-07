from django.urls import path

from login.views import LoginFormView, LogoutRedirectView

urlpatterns = [
    # Login
    path('login/', LoginFormView.as_view(), name='login'),
    # Logout
    path('logout/', LogoutRedirectView.as_view(), name='logout'),
]