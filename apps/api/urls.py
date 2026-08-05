from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from apps.api.views import (
    EarlyWarningListAPIView,
    ForecastAPIView,
    ScientificPublicationListAPIView,
    ServiceListAPIView,
    StationListAPIView,
    StationObservationView,
    StormWarningListAPIView,
    TropicalCycloneListAPIView,
    WeatherReportListAPIView,
)

router = DefaultRouter()

urlpatterns = router.urls + [
    # Autenticacion
    path('auth/', include('rest_framework.urls')),
    # Documentacion
    path('doc/', SpectacularSwaggerView.as_view(url_name='schema'), name='doc'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Estaciones
    path('stations/', StationListAPIView.as_view(), name='station-list'),
    path(
        'station/observation/<str:hour>/<int:station_number>/',
        StationObservationView.as_view(),
        name='station-observation',
    ),
    # Pronosticos
    path('forecast/<str:date>/', ForecastAPIView.as_view(), name='forecast'),
    # Avisos
    path('early-warnings/', EarlyWarningListAPIView.as_view(), name='early-warning-list'),
    path('tropical-cyclones/', TropicalCycloneListAPIView.as_view(), name='tropical-cyclone-list'),
    path('storm-warnings/', StormWarningListAPIView.as_view(), name='storm-warning-list'),
    # Reportes Meteorologicos
    path(
        'weather-reports/<str:type>/',
        WeatherReportListAPIView.as_view(),
        name='weather-report-list',
    ),
    # Publicaciones
    path('publications/', ScientificPublicationListAPIView.as_view(), name='publication-list'),
    # Servicios
    path('services/', ServiceListAPIView.as_view(), name='service-list'),
]
