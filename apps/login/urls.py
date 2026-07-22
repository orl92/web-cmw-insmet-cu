from django.urls import path

from apps.login.views import LoginFormView, LogoutRedirectView

app_name = 'login'

urlpatterns = [
    path('login/', LoginFormView.as_view(), name='in'),
    path('logout/', LogoutRedirectView.as_view(), name='out'),
]