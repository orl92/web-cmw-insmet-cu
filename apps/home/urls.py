from django.urls import path

from apps.home.views.avisos.alertas_tempranas.views import EarlyWarningListView
from apps.home.views.avisos.ciclones_tropicales.views import TropicalCycloneListView
from apps.home.views.avisos.tormentas.views import StormListView
from apps.home.views.home.views import IndexView
from apps.home.views.institucion.publicaciones.views import ScientificPublicationListView
from apps.home.views.modelos.views import (
    DescargarGifView,
    ImageProxyModeloView,
    MapaView,
    MeteogramView,
    SoundingView,
)
from apps.home.views.pago.views import PagoView
from apps.home.views.satelites.views import ProxyImageView, SateliteView
from apps.home.views.servicios.comerciales.views import (
    CommercialServicesListView,
    PublicCommercialServicesListView,
    ServiceDetailView,
)
from apps.home.views.servicios.publicos.views import PublicServicesListView
from apps.home.views.tiempo.views import WeatherReportDetailView

app_name = 'home'

urlpatterns = [
    # Inicio
    path('', IndexView.as_view(), name='index'),
    # Tiempo
    path(
        'tiempo/hoy/',
        WeatherReportDetailView.as_view(),
        {'report_type': 'today'},
        name='weather_today',
    ),
    path(
        'tiempo/manana/',
        WeatherReportDetailView.as_view(),
        {'report_type': 'tomorrow'},
        name='weather_tomorrow',
    ),
    # Comentario
    path(
        'comentario/tiempo/',
        WeatherReportDetailView.as_view(),
        {'report_type': 'commentary'},
        name='weather_commentary',
    ),
    path(
        'nota/meteorologica/',
        WeatherReportDetailView.as_view(),
        {'report_type': 'note'},
        name='weather_note',
    ),
    # Avisos
    path('aviso/alerta_temprana/', EarlyWarningListView.as_view(), name='warnings_early'),
    path('aviso/ciclon_tropical/', TropicalCycloneListView.as_view(), name='warnings_tropical'),
    path('aviso/tormenta/', StormListView.as_view(), name='warnings_storm'),
    # Modelos
    path('modelo/mapas/', MapaView.as_view(), name='models_maps'),
    path('modelo/meteogram/', MeteogramView.as_view(), name='models_meteogram'),
    path('modelo/sounding/', SoundingView.as_view(), name='models_sounding'),
    # Servicios Públicos
    path('servicios/publicos/', PublicServicesListView.as_view(), name='services_public'),
    # Servicios Comerciales
    path(
        'servicios/comerciales/', CommercialServicesListView.as_view(), name='services_commercial'
    ),
    path(
        'servicios/comerciales/public/',
        PublicCommercialServicesListView.as_view(),
        name='services_commercial_public',
    ),
    path(
        'servicio/comercial/<uuid:uuid>/',
        ServiceDetailView.as_view(),
        name='services_commercial_detail',
    ),
    # Imagen Satélites
    path('imagenes/satelitales/', SateliteView.as_view(), name='satellite'),
    path('proxy_image/', ProxyImageView.as_view(), name='proxy_image'),
    # Pagos en linea
    path('pago_en_linea/', PagoView.as_view(), name='payment'),
    # Institución
    path(
        'institucion/publicaciones_cientificas/',
        ScientificPublicationListView.as_view(),
        name='publications',
    ),
    # Otros
    path('proxy_image_modelo/', ImageProxyModeloView.as_view(), name='proxy_image_modelo'),
    path('modelo/descargar_gif/', DescargarGifView.as_view(), name='models_download_gif'),
]
