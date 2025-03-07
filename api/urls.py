from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)
from rest_framework.routers import DefaultRouter

from api.views import (ForecastAPIView, StationListAPIView,
                       StationObservationView)

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
    path('station/observation/<str:hour>/<int:station_number>/', StationObservationView.as_view(), name='station-observation'),
    # Pronosticos
    path('forecast/<str:date>/', ForecastAPIView.as_view(), name='forecast'),
]