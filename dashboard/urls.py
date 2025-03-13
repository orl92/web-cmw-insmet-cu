from django.urls import path

from dashboard.views.avisos.alertas_tempranas.views import (
    EarlyWarningCreateView, EarlyWarningDeleteView, EarlyWarningListView,
    EarlyWarningUpdateView)
from dashboard.views.avisos.ciclones_tropicales.views import (
    TropicalCycloneCreateView, TropicalCycloneDeleteView,
    TropicalCycloneListView, TropicalCycloneUpdateView)
from dashboard.views.avisos.especiales.views import (SpecialNoticeCreateView,
                                                     SpecialNoticeDeleteView,
                                                     SpecialNoticeListView,
                                                     SpecialNoticeUpdateView)
from dashboard.views.avisos.radares.views import (RadarWarningCreateView,
                                                  RadarWarningDeleteView,
                                                  RadarWarningListView,
                                                  RadarWarningUpdateView)
from dashboard.views.clientes.views import (CustomerCreateView,
                                            CustomerDeleteView,
                                            CustomerListView,
                                            CustomerUpdateView)
from dashboard.views.comentarios.nota_meteorologica.views import (
    WeatherNoteCreateView, WeatherNoteDeleteView, WeatherNoteListView,
    WeatherNoteUpdateView)
from dashboard.views.comentarios.tiempo.views import (
    WeatherCommentaryCreateView, WeatherCommentaryDeleteView,
    WeatherCommentaryListView, WeatherCommentaryUpdateView)
from dashboard.views.dashboard.views import DashboardView, ExcelJSONView
from dashboard.views.estaciones.views import (StationCreateView,
                                              StationDeleteView,
                                              StationListView,
                                              StationUpdateView)
from dashboard.views.pronosticos.views import (AllForecastCreateView,
                                               ForecastDeleteView,
                                               ForecastsListView,
                                               ForecastUpdateView)
from dashboard.views.provincias.views import (ProvinceCreateView,
                                              ProvinceDeleteView,
                                              ProvinceListView,
                                              ProvinceUpdateView)
from dashboard.views.servicios.views import (ServiceCreateView,
                                             ServiceDeleteView,
                                             ServiceListView,
                                             ServiceUpdateView)
from dashboard.views.tiempo.hoy.views import (WeatherTodayCreateView,
                                              WeatherTodayDeleteView,
                                              WeatherTodayListView,
                                              WeatherTodayUpdateView)
from dashboard.views.tiempo.manana.views import (WeatherTomorrowCreateView,
                                                 WeatherTomorrowDeleteView,
                                                 WeatherTomorrowListView,
                                                 WeatherTomorrowUpdateView)

urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name="dashboard"),
    # Provincias
    path('provincias/', ProvinceListView.as_view(), name='provincias'),
    path('crear/provincia/', ProvinceCreateView.as_view(), name='crear_provincia'),
    path('actualizar/provincia/<uuid:uuid>//', ProvinceUpdateView.as_view(), name='actualizar_provincia'),
    path('eliminar/provincia/<uuid:uuid>/', ProvinceDeleteView.as_view(), name='eliminar_provincia'),
    # Estaciones
    path('estaciones/', StationListView.as_view(), name='estaciones'),
    path('crear/estacion/', StationCreateView.as_view(), name='crear_estacion'),
    path('actualizar/estacion/<uuid:uuid>//', StationUpdateView.as_view(), name='actualizar_estacion'),
    path('eliminar/estacion/<uuid:uuid>/', StationDeleteView.as_view(), name='eliminar_estacion'),
    # Pronósticos
    path('pronosticos/', ForecastsListView.as_view(), name='pronosticos'),
    path('crear/pronostico/', AllForecastCreateView.as_view(), name='crear_pronostico'),
    path('actualizar/pronostico/<uuid:uuid>/', ForecastUpdateView.as_view(), name='actualizar_pronostico'),
    path('eliminar/pronostico/<uuid:uuid>/', ForecastDeleteView.as_view(), name='eliminar_pronostico'),
    # Excel json
    path('excel/json/', ExcelJSONView.as_view(), name='excel_json'),
    # Aviso Alerta Temprana
    path('avisos/alertas_tempranas/', EarlyWarningListView.as_view(), name='alertas_tempranas'),
    path('crear/aviso/alerta_temprana/', EarlyWarningCreateView.as_view(), name="crear_aviso_alerta_temprana"),
    path('actualizar/aviso/alerta_temprana/<uuid:uuid>/', EarlyWarningUpdateView.as_view(), name='actualizar_aviso_alerta_temprana'),
    path('eliminar/aviso/alerta_temprana/<uuid:uuid>/', EarlyWarningDeleteView.as_view(), name='eliminar_aviso_alerta_temprana'),
    # Aviso Ciclón Tropical
    path('avisos/ciclones_tropicales/', TropicalCycloneListView.as_view(), name='ciclones_tropicales'),
    path('crear/aviso/ciclon_tropical/', TropicalCycloneCreateView.as_view(), name="crear_aviso_ciclon_tropical"),
    path('actualizar/aviso/ciclon_tropical/<uuid:uuid>/',TropicalCycloneUpdateView.as_view(), name='actualizar_aviso_ciclon_tropical'),
    path('eliminar/aviso/ciclon_tropical/<uuid:uuid>/',TropicalCycloneDeleteView.as_view(), name='eliminar_aviso_ciclon_tropical'),
    # Aviso Especial
    path('avisos/especiales/', SpecialNoticeListView.as_view(), name='avisos_especiales'),
    path('crear/aviso/especial/', SpecialNoticeCreateView.as_view(), name="crear_aviso_especial"),
    path('actualizar/aviso/especial/<uuid:uuid>/', SpecialNoticeUpdateView.as_view(), name='actualizar_aviso_especial'),
    path('eliminar/aviso/especial/<uuid:uuid>/',SpecialNoticeDeleteView.as_view(), name='eliminar_aviso_especial'),
    # Avisos Radar
    path('avisos/radares/', RadarWarningListView.as_view(), name='avisos_radares'),
    path('crear/aviso/radar/', RadarWarningCreateView.as_view(), name="crear_aviso_radar"),
    path('actualizar/aviso/radar/<uuid:uuid>/', RadarWarningUpdateView.as_view(), name='actualizar_aviso_radar'),
    path('eliminar/aviso/radar/<uuid:uuid>/', RadarWarningDeleteView.as_view(), name='eliminar_aviso_radar'),
    # Clientes
    path('clientes/', CustomerListView.as_view(), name='listado_clientes'), 
    path('crear/cliente/', CustomerCreateView.as_view(), name='crear_cliente'),
    path('actualizar/cliente/<uuid:uuid>/', CustomerUpdateView.as_view(), name='actualizar_cliente'),
    path('eliminar/cliente/<uuid:uuid>/', CustomerDeleteView.as_view(), name='eliminar_cliente'),
    # Servicios
    path('servicios/', ServiceListView.as_view(), name='listado_servicios'), 
    path('crear/servicio/', ServiceCreateView.as_view(), name="crear_servicio"),
    path('actualizar/servicio/<uuid:uuid>/', ServiceUpdateView.as_view(), name='actualizar_servicio'),
    path('eliminar/servicio/<uuid:uuid>/', ServiceDeleteView.as_view(), name='eliminar_servicio'),
    # Tiempo Hoy
    path('tiempo/hoy/', WeatherTodayListView.as_view(), name='listado_tiempo_h'), 
    path('crear/tiempo/hoy/', WeatherTodayCreateView.as_view(), name="crear_tiempo_h"),
    path('actualizar/tiempo/hoy/<uuid:uuid>/', WeatherTodayUpdateView.as_view(), name='actualizar_tiempo_h'),
    path('eliminar/tiempo/hoy/<uuid:uuid>/', WeatherTodayDeleteView.as_view(), name='eliminar_tiempo_h'),
    # Tiempo Mañana
    path('tiempo/manana/', WeatherTomorrowListView.as_view(), name='listado_tiempo_m'),
    path('crear/tiempo/manana/', WeatherTomorrowCreateView.as_view(), name="crear_tiempo_m"),
    path('actualizar/tiempo/manana/<uuid:uuid>/', WeatherTomorrowUpdateView.as_view(), name='actualizar_tiempo_m'),
    path('eliminar/tiempo/manana/<uuid:uuid>/', WeatherTomorrowDeleteView.as_view(), name='eliminar_tiempo_m'),
    # Comentario Tiempo
    path('comentario/tiempo/', WeatherCommentaryListView.as_view(), name='listado_comentarios_tiempo'), 
    path('crear/comentario/tiempo/', WeatherCommentaryCreateView.as_view(), name="crear_comentario_tiempo"),
    path('actualizar/comentario/tiempo/<uuid:uuid>/', WeatherCommentaryUpdateView.as_view(), name='actualizar_comentario_tiempo'),
    path('eliminar/comentario/tiempo/<uuid:uuid>/', WeatherCommentaryDeleteView.as_view(), name='eliminar_comentario_tiempo'),
    # Nota Meteorológica
    path('nota/meteorologica/', WeatherNoteListView.as_view(), name='listado_notas_meteorologicas'), 
    path('crear/nota/meteorologica/', WeatherNoteCreateView.as_view(), name="crear_nota_meteorologica"),
    path('actualizar/nota/meteorologica/<uuid:uuid>/', WeatherNoteUpdateView.as_view(), name='actualizar_nota_meteorologica'),
    path('eliminar/nota/meteorologica/<uuid:uuid>/', WeatherNoteDeleteView.as_view(), name='eliminar_nota_meteorologica'),
]
