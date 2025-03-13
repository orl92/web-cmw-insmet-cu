from django.urls import path

from home.views.avisos.alertas_tempranas.views import EarlyWarningListView
from home.views.avisos.ciclones_tropicales.views import TropicalCycloneListView
from home.views.avisos.especiales.views import SpecialNoticeListView
from home.views.avisos.radares.views import RadarWarningListView
from home.views.comentarios.nota_meteorologica.views import \
    WeatherNoteDetailView
from home.views.comentarios.tiempo.views import WeatherCommentaryDetailView
from home.views.home.views import IndexView
from home.views.mapas.views import *
from home.views.satelites.views import ProxyImageView, SateliteView
from home.views.servicios.comerciales.views import CommercialServicesListView
from home.views.servicios.publicos.views import PublicServicesListView
from home.views.tiempo.hoy.views import WeatherTodayDetailView
from home.views.tiempo.manana.views import WeatherTomorrowDetailView

urlpatterns = [
    # Inicio
    path('', IndexView.as_view(), name="index"),
    # Tiempo
    path('tiempo/hoy/', WeatherTodayDetailView.as_view(), name="tiempo_h"),
    path('tiempo/manana/', WeatherTomorrowDetailView.as_view(), name="tiempo_m"),
    # Comentario
    path('comentario/tiempo/', WeatherCommentaryDetailView.as_view(), name="comentario_tiempo"),
    path('nota/meteorologica/', WeatherNoteDetailView.as_view(), name="nota_meteorologica"),
    # Avisos
    path('aviso/alerta_temprana/', EarlyWarningListView.as_view(), name="alerta_temprana"),
    path('aviso/ciclon_tropical/', TropicalCycloneListView.as_view(), name="ciclon_tropical"),
    path('aviso/especial/', SpecialNoticeListView.as_view(), name="especial"),
    path('aviso/radar/', RadarWarningListView.as_view(), name="radar"),
    # Mapas
    path('mapa/niveles/', MapaNivelView.as_view(), name="niveles"),
    path('mapa/sinoptico/', MapaSinopticoView.as_view(), name="sinoptico"),
    path('mapa/sinoptico_atlantico/', MapaSinopticoAtlanticoView.as_view(), name="sinoptico_atlantico"),
    path('mapa/tri_horario/', MapaTriHorarioView.as_view(), name="tri_horario"),
    path('mapa/tiempo/', MapaTvView.as_view(), name="tiempo"),
    path('mapa/viento/', MapaVientoView.as_view(), name="viento"),
    # Servicios Públicos
    path('servicios/publicos/', PublicServicesListView.as_view(), name='servicios_publicos'),
     # Servicios Comerciales
    path('servicios/comerciales/', CommercialServicesListView.as_view(), name='servicios_comerciales'),
    # Imagen Satélites
    path('imagenes/satelitales/', SateliteView.as_view(), name="satelites"),
    path('proxy_image/', ProxyImageView.as_view(), name='proxy_image'),
]