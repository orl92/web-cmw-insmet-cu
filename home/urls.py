from django.urls import path

from home.views.avisos.alertas_tempranas.views import EarlyWarningListView
from home.views.avisos.ciclones_tropicales.views import TropicalCycloneListView
from home.views.avisos.tormentas.views import StormListView
from home.views.home.views import IndexView
from home.views.tiempo.views import WeatherReportDetailView
from home.views.institucion.publicaciones.views import ScientificPublicationListView
from home.views.modelos.views import (
    DescargarGifView,
    ImageProxyModeloView,
    MapaView,
    MeteogramView,
    SoundingView,
)
from home.views.pago.views import PagoView
from home.views.satelites.views import ProxyImageView, SateliteView
from home.views.servicios.comerciales.views import (
    CommercialServicesListView,
    PublicCommercialServicesListView,
    ServiceDetailView,
)
from home.views.servicios.publicos.views import PublicServicesListView

urlpatterns = [
    # Inicio
    path('', IndexView.as_view(), name="index"),
    # Tiempo
    path('tiempo/hoy/', WeatherReportDetailView.as_view(), {'report_type': 'today'}, name="tiempo_h"),
    path('tiempo/manana/', WeatherReportDetailView.as_view(), {'report_type': 'tomorrow'}, name="tiempo_m"),
    # Comentario
    path('comentario/tiempo/', WeatherReportDetailView.as_view(), {'report_type': 'commentary'}, name="comentario_tiempo"),
    path('nota/meteorologica/', WeatherReportDetailView.as_view(), {'report_type': 'note'}, name="nota_meteorologica"),
    # Avisos
    path('aviso/alerta_temprana/', EarlyWarningListView.as_view(), name="alerta_temprana"),
    path('aviso/ciclon_tropical/', TropicalCycloneListView.as_view(), name="ciclon_tropical"),
    path('aviso/tormenta/', StormListView.as_view(), name="tormenta"),
    # Modelos
    path('modelo/mapas/', MapaView.as_view(), name='maps'),
    path('modelo/meteogram/', MeteogramView.as_view(), name='meteogram'),
    path('modelo/sounding/', SoundingView.as_view(), name='sounding'),
    # Servicios Públicos
    path('servicios/publicos/', PublicServicesListView.as_view(), name='servicios_publicos'),
    # Servicios Comerciales
    path('servicios/comerciales/', CommercialServicesListView.as_view(), name='servicios_comerciales'),
    path('servicios/comerciales/public/', PublicCommercialServicesListView.as_view(), name='public_servicios_comerciales'),
    path('servicio/comercial/<uuid:uuid>/', ServiceDetailView.as_view(), name='detalle_servicio_comercial'),
    # Imagen Satélites
    path('imagenes/satelitales/', SateliteView.as_view(), name="satelites"),
    path('proxy_image/', ProxyImageView.as_view(), name='proxy_image'),
    # Pagos en linea
    path('pago_en_linea/', PagoView.as_view(), name='pago_qr'),
    # Institución
    path('institucion/publicaciones_cientificas/', ScientificPublicationListView.as_view(), name='publicaciones_cientificas'),
    # Otros   
    path('proxy_image_modelo/', ImageProxyModeloView.as_view(), name='proxy_image_modelo'),
    path('modelo/descargar_gif/', DescargarGifView.as_view(), name='descargar_gif'),

]
