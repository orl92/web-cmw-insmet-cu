from django.urls import path

from apps.dashboard.views.dashboard.dashboard import DashboardView, TaskMonitoringView

app_name = 'dashboard'

urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name='index'),
    # Monitoreo de tareas asíncronas (Huey)
    path('tasks/', TaskMonitoringView.as_view(), name='tasks'),
]
