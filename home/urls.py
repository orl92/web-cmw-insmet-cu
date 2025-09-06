from django.urls import path

from home.views.avisos.alertas_tempranas.views import EarlyWarningListView
from home.views.avisos.ciclones_tropicales.views import TropicalCycloneListView
from home.views.avisos.tormentas.views import StormListView
from home.views.avisos.radares.views import RadarWarningListView
from home.views.comentarios.nota_meteorologica.views import \
    WeatherNoteDetailView
from home.views.comentarios.tiempo.views import WeatherCommentaryDetailView
from home.views.home.views import IndexView
from home.views.modelos.views import MapaView, MeteogramView, SoundingView
from home.views.satelites.views import ProxyImageView, SateliteView
from home.views.servicios.comerciales.views import CommercialServicesListView
from home.views.servicios.publicos.views import PublicServicesListView
from home.views.tiempo.hoy.views import WeatherTodayDetailView
from home.views.tiempo.manana.views import WeatherTomorrowDetailView

from home.views.modelos import views

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
    path('aviso/tormenta/', StormListView.as_view(), name="tormenta"),
    path('aviso/radar/', RadarWarningListView.as_view(), name="radar"),
    # Modelos
    path('modelo/mapas/', MapaView.as_view(), name='maps'),
    path('modelo/meteogram/', MeteogramView.as_view(), name='meteogram'),
    path('modelo/sounding/', SoundingView.as_view(), name='sounding'),
    # Servicios Públicos
    path('servicios/publicos/', PublicServicesListView.as_view(), name='servicios_publicos'),
    # Servicios Comerciales
    path('servicios/comerciales/', CommercialServicesListView.as_view(), name='servicios_comerciales'),
    # Imagen Satélites
    path('imagenes/satelitales/', SateliteView.as_view(), name="satelites"),
    path('proxy_image/', ProxyImageView.as_view(), name='proxy_image'),

]
