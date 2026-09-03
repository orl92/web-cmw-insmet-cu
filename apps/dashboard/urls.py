from django.urls import path

from apps.dashboard.views.dashboard.dashboard import (
    DashboardView,
    TaskMonitoringActionView,
    TaskMonitoringView,
)

app_name = 'dashboard'

urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name='index'),
    # Monitoreo de tareas asíncronas (Huey)
    path('tasks/', TaskMonitoringView.as_view(), name='tasks'),
    # Acciones sobre un registro de tarea (reintentar/limpiar)
    path('tasks/<int:pk>/action/', TaskMonitoringActionView.as_view(), name='tasks_action'),
]
