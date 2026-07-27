from django.urls import path

from apps.dashboard.views.dashboard.dashboard import DashboardView

app_name = 'dashboard'

urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name="index"),
]
