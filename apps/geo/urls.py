from django.urls import path

from apps.geo.views import (
    ProvinceCreateView,
    ProvinceDeleteView,
    ProvinceListView,
    ProvinceUpdateView,
    StationCreateView,
    StationDeleteView,
    StationListView,
    StationUpdateView,
    TownCreateView,
    TownDeleteView,
    TownListView,
    TownUpdateView,
)


app_name = 'geo'

urlpatterns = [
    path('provincias/', ProvinceListView.as_view(), name='provincia_list'),
    path('crear/provincia/', ProvinceCreateView.as_view(), name='provincia_create'),
    path('actualizar/provincia/<uuid:uuid>/', ProvinceUpdateView.as_view(), name='provincia_update'),
    path('eliminar/provincia/<uuid:uuid>/', ProvinceDeleteView.as_view(), name='provincia_delete'),
    path('estaciones/', StationListView.as_view(), name='estacion_list'),
    path('crear/estacion/', StationCreateView.as_view(), name='estacion_create'),
    path('actualizar/estacion/<uuid:uuid>/', StationUpdateView.as_view(), name='estacion_update'),
    path('eliminar/estacion/<uuid:uuid>/', StationDeleteView.as_view(), name='estacion_delete'),
    path('municipios/', TownListView.as_view(), name='municipio_list'),
    path('crear/municipio/', TownCreateView.as_view(), name='municipio_create'),
    path('actualizar/municipio/<uuid:uuid>/', TownUpdateView.as_view(), name='municipio_update'),
    path('eliminar/municipio/<uuid:uuid>/', TownDeleteView.as_view(), name='municipio_delete'),
]
