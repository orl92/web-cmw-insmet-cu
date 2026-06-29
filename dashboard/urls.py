from django.urls import path

from dashboard.views.avisos.alertas_tempranas.views import (
    EarlyWarningCreateView,
    EarlyWarningDeleteView,
    EarlyWarningListView,
    EarlyWarningUpdateView,
)
from dashboard.views.avisos.ciclones_tropicales.views import (
    TropicalCycloneCreateView,
    TropicalCycloneDeleteView,
    TropicalCycloneListView,
    TropicalCycloneUpdateView,
)
from dashboard.views.avisos.tormentas.views import (
    StormWarningCreateView,
    StormWarningDeleteView,
    StormWarningListView,
    StormWarningUpdateView,
)
from dashboard.views.clientes.views import (
    CustomerCreateView,
    CustomerDeleteView,
    CustomerListView,
    CustomerUpdateView,
)
from dashboard.views.comentarios.nota_meteorologica.views import (
    WeatherNoteCreateView,
    WeatherNoteDeleteView,
    WeatherNoteListView,
    WeatherNoteUpdateView,
)
from dashboard.views.comentarios.tiempo.views import (
    WeatherCommentaryCreateView,
    WeatherCommentaryDeleteView,
    WeatherCommentaryListView,
    WeatherCommentaryUpdateView,
)
from dashboard.views.company.views import CompanySettingsUpdateView
from dashboard.views.dashboard.views import (
    DashboardView,
    ExcelJSONView,
    MaintenanceModeToggleView,
)
from dashboard.views.email_recipient.views import (
    EmailRecipientListCreateView,
    EmailRecipientListDeleteView,
    EmailRecipientListListView,
    EmailRecipientListUpdateView,
)
from dashboard.views.estaciones.views import (
    StationCreateView,
    StationDeleteView,
    StationListView,
    StationUpdateView,
)
from dashboard.views.facturacion.views import (
    CompanySettingsAjaxUpdateView,
    InvoiceCreateView,
    InvoiceListView,
    ajax_pending_subscriptions,
)
from dashboard.views.municipios.views import (
    TownCreateView,
    TownDeleteView,
    TownListView,
    TownUpdateView,
)
from dashboard.views.pronosticos.views import (
    AllForecastCreateView,
    ForecastDeleteView,
    ForecastsListView,
    ForecastUpdateView,
)
from dashboard.views.provincias.views import (
    ProvinceCreateView,
    ProvinceDeleteView,
    ProvinceListView,
    ProvinceUpdateView,
)
from dashboard.views.publicaciones.views import (
    ScientificPublicationCreateView,
    ScientificPublicationDeleteView,
    ScientificPublicationDetailView,
    ScientificPublicationListView,
    ScientificPublicationPDFView,
    ScientificPublicationUpdateView,
)
from dashboard.views.servicios.views import (
    ServiceCreateView,
    ServiceDeleteView,
    ServiceListView,
    ServiceUpdateView,
)
from dashboard.views.suscripciones.views import (
    ApproveSubscriptionView,
    GenerateInvoiceView,
    RegenerateInvoiceView,
    SubscriptionCreateView,
    SubscriptionDeleteView,
    SubscriptionListView,
    SubscriptionRenewView,
    SubscriptionUpdateView,
)
from dashboard.views.tiempo.hoy.views import (
    WeatherTodayCreateView,
    WeatherTodayDeleteView,
    WeatherTodayDetailView,
    WeatherTodayListView,
    WeatherTodayPDFView,
    WeatherTodayUpdateView,
)
from dashboard.views.tiempo.manana.views import (
    WeatherTomorrowCreateView,
    WeatherTomorrowDeleteView,
    WeatherTomorrowDetailView,
    WeatherTomorrowListView,
    WeatherTomorrowPDFView,
    WeatherTomorrowUpdateView,
)

urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name="dashboard"),
    # Provincias
    path('provincias/', ProvinceListView.as_view(), name='provincias'),
    path('crear/provincia/', ProvinceCreateView.as_view(), name='crear_provincia'),
    path('actualizar/provincia/<uuid:uuid>/', ProvinceUpdateView.as_view(), name='actualizar_provincia'),
    path('eliminar/provincia/<uuid:uuid>/', ProvinceDeleteView.as_view(), name='eliminar_provincia'),
    # Estaciones
    path('estaciones/', StationListView.as_view(), name='estaciones'),
    path('crear/estacion/', StationCreateView.as_view(), name='crear_estacion'),
    path('actualizar/estacion/<uuid:uuid>/', StationUpdateView.as_view(), name='actualizar_estacion'),
    path('eliminar/estacion/<uuid:uuid>/', StationDeleteView.as_view(), name='eliminar_estacion'),
    # Municipios
    path('municipios/', TownListView.as_view(), name='municipios'),
    path('crear/municipio/', TownCreateView.as_view(), name='crear_municipio'),
    path('actualizar/municipio/<uuid:uuid>/', TownUpdateView.as_view(), name='actualizar_municipio'),
    path('eliminar/municipio/<uuid:uuid>/', TownDeleteView.as_view(), name='eliminar_municipio'),
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
    path('actualizar/aviso/ciclon_tropical/<uuid:uuid>/', TropicalCycloneUpdateView.as_view(), name='actualizar_aviso_ciclon_tropical'),
    path('eliminar/aviso/ciclon_tropical/<uuid:uuid>/', TropicalCycloneDeleteView.as_view(), name='eliminar_aviso_ciclon_tropical'),
    # Aviso Tormenta
    path('avisos/tormentas/', StormWarningListView.as_view(), name='avisos_tormentas'),
    path('crear/aviso/tormenta/', StormWarningCreateView.as_view(), name="crear_aviso_tormenta"),
    path('actualizar/aviso/tormenta/<uuid:uuid>/', StormWarningUpdateView.as_view(), name='actualizar_aviso_tormenta'),
    path('eliminar/aviso/tormenta/<uuid:uuid>/', StormWarningDeleteView.as_view(), name='eliminar_aviso_tormenta'),
    # Clientes
    path('clientes/', CustomerListView.as_view(), name='listado_clientes'),
    path('crear/cliente/', CustomerCreateView.as_view(), name='crear_cliente'),
    path('actualizar/cliente/<uuid:uuid>/', CustomerUpdateView.as_view(), name='actualizar_cliente'),
    path('eliminar/cliente/<uuid:uuid>/', CustomerDeleteView.as_view(), name='eliminar_cliente'),
    # Servicios
    path('servicios/', ServiceListView.as_view(), name='listado_servicios'),
    path('crear/servicios/', ServiceCreateView.as_view(), name='crear_servicio'),
    path('actualizar/servicios/<uuid:uuid>/', ServiceUpdateView.as_view(), name='actualizar_servicio'),
    path('eliminar/servicios/<uuid:uuid>/', ServiceDeleteView.as_view(), name='eliminar_servicio'),
    # Suscripciones
    path('suscripciones/', SubscriptionListView.as_view(), name='listado_suscripciones'),
    path('crear/suscripcion/', SubscriptionCreateView.as_view(), name='crear_suscripcion'),
    path('actualizar/suscripcion/<uuid:uuid>/', SubscriptionUpdateView.as_view(), name='editar_suscripcion'),
    path('eliminar/suscripcion/<uuid:uuid>/', SubscriptionDeleteView.as_view(), name='eliminar_suscripcion'),
    path('renovar/suscripcion/<uuid:uuid>/', SubscriptionRenewView.as_view(), name='renovar_suscripcion'),
    path('facturar/suscripcion/<uuid:uuid>/', GenerateInvoiceView.as_view(), name='facturar_suscripcion'),
    path('regenerar-factura/<uuid:uuid>/', RegenerateInvoiceView.as_view(), name='regenerar_factura'),
    path('aprobar/suscripcion/<uuid:uuid>/', ApproveSubscriptionView.as_view(), name='aprobar_suscripcion'),
    # Facturación
    path('facturacion/', InvoiceListView.as_view(), name='listado_facturas'),
    path('crear/factura/', InvoiceCreateView.as_view(), name='crear_factura'),
    path('ajax/suscripciones-pendientes/', ajax_pending_subscriptions, name='ajax_pending_subscriptions'),
    # Tiempo Hoy
    path('tiempo/hoy/', WeatherTodayListView.as_view(), name='listado_tiempo_h'),
    path('crear/tiempo/hoy/', WeatherTodayCreateView.as_view(), name="crear_tiempo_h"),
    path('actualizar/tiempo/hoy/<uuid:uuid>/', WeatherTodayUpdateView.as_view(), name='actualizar_tiempo_h'),
    path('eliminar/tiempo/hoy/<uuid:uuid>/', WeatherTodayDeleteView.as_view(), name='eliminar_tiempo_h'),
    path('detalle/tiempo/hoy/<uuid:uuid>/', WeatherTodayDetailView.as_view(), name='detalle_tiempo_h'),
    path('tiempo/hoy/<uuid:uuid>/pdf/', WeatherTodayPDFView.as_view(), name='tiempo_h_pdf'),
    # Tiempo Mañana
    path('tiempo/manana/', WeatherTomorrowListView.as_view(), name='listado_tiempo_m'),
    path('crear/tiempo/manana/', WeatherTomorrowCreateView.as_view(), name="crear_tiempo_m"),
    path('actualizar/tiempo/manana/<uuid:uuid>/', WeatherTomorrowUpdateView.as_view(), name='actualizar_tiempo_m'),
    path('eliminar/tiempo/manana/<uuid:uuid>/', WeatherTomorrowDeleteView.as_view(), name='eliminar_tiempo_m'),
    path('detalle/tiempo/manana/<uuid:uuid>/', WeatherTomorrowDetailView.as_view(), name='detalle_tiempo_m'),
    path('tiempo/manana/<uuid:uuid>/pdf/', WeatherTomorrowPDFView.as_view(), name='tiempo_m_pdf'),
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
    # Listado de Correos
    path('listado/correos/', EmailRecipientListListView.as_view(), name='listado_correos'),
    path('crear/listado/correo/', EmailRecipientListCreateView.as_view(), name='crear_listado_correo'),
    path('actualizar/listado/correo/<uuid:uuid>/', EmailRecipientListUpdateView.as_view(), name='actualizar_listado_correo'),
    path('eliminar/listado/correo/<uuid:uuid>/', EmailRecipientListDeleteView.as_view(), name='eliminar_listado_correo'),
    # Configuracion Empresa
    path('configuracion/empresa/', CompanySettingsUpdateView.as_view(), name='company_settings'),
    path('configuracion/empresa/ajax/', CompanySettingsAjaxUpdateView.as_view(), name='company_settings_ajax'),
    # Modo Mantenimiento
    path('toggle-maintenance/', MaintenanceModeToggleView.as_view(), name='toggle_maintenance_mode'),
    # Publicaciones Científicas (nuevo)
    path('publicaciones/', ScientificPublicationListView.as_view(), name='listado_publicaciones'),
    path('crear/publicacion/', ScientificPublicationCreateView.as_view(), name='crear_publicacion'),
    path('actualizar/publicacion/<uuid:uuid>/', ScientificPublicationUpdateView.as_view(), name='actualizar_publicacion'),
    path('eliminar/publicacion/<uuid:uuid>/', ScientificPublicationDeleteView.as_view(), name='eliminar_publicacion'),
    path('detalle/publicacion/<uuid:uuid>/', ScientificPublicationDetailView.as_view(), name='detalle_publicacion'),
    path('publicacion/<uuid:uuid>/pdf/', ScientificPublicationPDFView.as_view(), name='publicacion_pdf'),
]
