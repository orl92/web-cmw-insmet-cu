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
from dashboard.views.certificados.views import (
    CertificateCreateView,
    CertificateDeleteView,
    CertificateDetailView,
    CertificateListView,
    CertificatePDFView,
)
from dashboard.views.clientes.views import (
    CustomerCreateView,
    CustomerDeleteView,
    CustomerHardDeleteView,
    CustomerListView,
    CustomerUpdateView,
)
from dashboard.views.contratos.views import (
    ContractCreateView,
    ContractDeleteView,
    ContractDetailView,
    ContractListView,
)
from dashboard.views.company.views import CompanySettingsUpdateView
from dashboard.views.dashboard.views import (
    DashboardView,
    ExcelJSONView,
    MaintenanceModeToggleView,
)
from dashboard.views.exports import (
    CustomerCSVExportView,
    EarlyWarningCSVExportView,
    ForecastsCSVExportView,
    ForecastsExcelExportView,
    InvoiceCSVExportView,
    ServiceCSVExportView,
    ServiceSubscriptionCSVExportView,
    StormWarningCSVExportView,
    TropicalCycloneCSVExportView,
    WeatherReportCSVExportView,
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
    CancelInvoiceView,
    CompanySettingsAjaxUpdateView,
    ContractHardDeleteView,
    InvoiceCreateView,
    InvoiceHardDeleteView,
    InvoiceListView,
    ResendInvoiceEmailView,
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
    ServiceHardDeleteView,
    ServiceListView,
    ServiceUpdateView,
)
from dashboard.views.suscripciones.views import (
    ApproveSubscriptionView,
    CertificateHardDeleteView,
    RegenerateInvoiceView,
    ResendCertificateEmailView,
    SubscriptionCancelView,
    SubscriptionCreateView,
    SubscriptionHardDeleteView,
    SubscriptionListView,
    SubscriptionRenewView,
    SubscriptionUpdateView,
)
from dashboard.views.tiempo.views import (
    WeatherReportCreateView,
    WeatherReportDeleteView,
    WeatherReportDetailView,
    WeatherReportListView,
    WeatherReportPDFView,
    WeatherReportUpdateView,
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
    path('eliminar/cliente/<uuid:uuid>/permanente/', CustomerHardDeleteView.as_view(), name='eliminar_cliente_permanente'),
    path('clientes/exportar/csv/', CustomerCSVExportView.as_view(), name='exportar_csv_clientes'),
    # Servicios
    path('servicios/', ServiceListView.as_view(), name='listado_servicios'),
    path('crear/servicios/', ServiceCreateView.as_view(), name='crear_servicio'),
    path('actualizar/servicios/<uuid:uuid>/', ServiceUpdateView.as_view(), name='actualizar_servicio'),
    path('eliminar/servicios/<uuid:uuid>/', ServiceDeleteView.as_view(), name='eliminar_servicio'),
    path('eliminar/servicios/<uuid:uuid>/permanente/', ServiceHardDeleteView.as_view(), name='eliminar_servicio_permanente'),
    path('servicios/exportar/csv/', ServiceCSVExportView.as_view(), name='exportar_csv_servicios'),
    # Suscripciones
    path('suscripciones/', SubscriptionListView.as_view(), name='listado_suscripciones'),
    path('crear/suscripcion/', SubscriptionCreateView.as_view(), name='crear_suscripcion'),
    path('actualizar/suscripcion/<uuid:uuid>/', SubscriptionUpdateView.as_view(), name='editar_suscripcion'),
    path('anular/suscripcion/<uuid:uuid>/', SubscriptionCancelView.as_view(), name='anular_suscripcion'),
    path('eliminar/suscripcion/<uuid:uuid>/', SubscriptionHardDeleteView.as_view(), name='eliminar_suscripcion'),
    path('renovar/suscripcion/<uuid:uuid>/', SubscriptionRenewView.as_view(), name='renovar_suscripcion'),
    path('regenerar-factura/<uuid:uuid>/', RegenerateInvoiceView.as_view(), name='regenerar_factura'),
    path('aprobar/suscripcion/<uuid:uuid>/', ApproveSubscriptionView.as_view(), name='aprobar_suscripcion'),
    path('reenviar/certificado/<uuid:uuid>/', ResendCertificateEmailView.as_view(), name='reenviar_certificado'),
    # Certificados
    path('certificados/', CertificateListView.as_view(), name='listado_certificados'),
    path('crear/certificado/', CertificateCreateView.as_view(), name='crear_certificado'),
    path('detalle/certificado/<uuid:uuid>/', CertificateDetailView.as_view(), name='detalle_certificado'),
    path('certificado/<uuid:uuid>/pdf/', CertificatePDFView.as_view(), name='certificado_pdf'),
    path('eliminar/certificado/<uuid:uuid>/', CertificateDeleteView.as_view(), name='eliminar_certificado'),
    path('eliminar/certificado/<uuid:uuid>/permanente/', CertificateHardDeleteView.as_view(), name='eliminar_certificado_permanente'),
    path('suscripciones/exportar/csv/', ServiceSubscriptionCSVExportView.as_view(), name='exportar_csv_suscripciones'),
    # Facturación
    path('facturacion/', InvoiceListView.as_view(), name='listado_facturas'),
    path('crear/factura/', InvoiceCreateView.as_view(), name='crear_factura'),
    path('anular/factura/<uuid:uuid>/', CancelInvoiceView.as_view(), name='anular_factura'),
    path('eliminar/factura/<uuid:uuid>/', InvoiceHardDeleteView.as_view(), name='eliminar_factura'),
    path('reenviar/correo/factura/<uuid:uuid>/', ResendInvoiceEmailView.as_view(), name='reenviar_correo_factura'),
    path('ajax/suscripciones-pendientes/', ajax_pending_subscriptions, name='ajax_pending_subscriptions'),
    # Contratos
    path('contratos/', ContractListView.as_view(), name='listado_contratos'),
    path('crear/contrato/', ContractCreateView.as_view(), name='crear_contrato'),
    path('detalle/contrato/<uuid:uuid>/', ContractDetailView.as_view(), name='detalle_contrato'),
    path('eliminar/contrato/<uuid:uuid>/', ContractDeleteView.as_view(), name='eliminar_contrato'),
    path('eliminar/contrato/<uuid:uuid>/permanente/', ContractHardDeleteView.as_view(), name='eliminar_contrato_permanente'),
    path('facturacion/exportar/csv/', InvoiceCSVExportView.as_view(), name='exportar_csv_facturas'),
    path('pronosticos/exportar/csv/', ForecastsCSVExportView.as_view(), name='exportar_csv_pronosticos'),
    path('pronosticos/exportar/excel/', ForecastsExcelExportView.as_view(), name='exportar_excel_pronosticos'),
    path('tiempo/exportar/csv/', WeatherReportCSVExportView.as_view(), name='exportar_csv_tiempo'),
    path('avisos/alertas/exportar/csv/', EarlyWarningCSVExportView.as_view(), name='exportar_csv_alertas'),
    path('avisos/ciclones/exportar/csv/', TropicalCycloneCSVExportView.as_view(), name='exportar_csv_ciclones'),
    path('avisos/tormentas/exportar/csv/', StormWarningCSVExportView.as_view(), name='exportar_csv_tormentas'),
    # Tiempo Hoy
    path('tiempo/hoy/', WeatherReportListView.as_view(), {'report_type': 'today'}, name='listado_tiempo_h'),
    path('crear/tiempo/hoy/', WeatherReportCreateView.as_view(), {'report_type': 'today'}, name="crear_tiempo_h"),
    path('actualizar/tiempo/hoy/<uuid:uuid>/', WeatherReportUpdateView.as_view(), {'report_type': 'today'}, name='actualizar_tiempo_h'),
    path('eliminar/tiempo/hoy/<uuid:uuid>/', WeatherReportDeleteView.as_view(), {'report_type': 'today'}, name='eliminar_tiempo_h'),
    path('detalle/tiempo/hoy/<uuid:uuid>/', WeatherReportDetailView.as_view(), {'report_type': 'today'}, name='detalle_tiempo_h'),
    path('tiempo/hoy/<uuid:uuid>/pdf/', WeatherReportPDFView.as_view(), {'report_type': 'today'}, name='tiempo_h_pdf'),
    # Tiempo Mañana
    path('tiempo/manana/', WeatherReportListView.as_view(), {'report_type': 'tomorrow'}, name='listado_tiempo_m'),
    path('crear/tiempo/manana/', WeatherReportCreateView.as_view(), {'report_type': 'tomorrow'}, name="crear_tiempo_m"),
    path('actualizar/tiempo/manana/<uuid:uuid>/', WeatherReportUpdateView.as_view(), {'report_type': 'tomorrow'}, name='actualizar_tiempo_m'),
    path('eliminar/tiempo/manana/<uuid:uuid>/', WeatherReportDeleteView.as_view(), {'report_type': 'tomorrow'}, name='eliminar_tiempo_m'),
    path('detalle/tiempo/manana/<uuid:uuid>/', WeatherReportDetailView.as_view(), {'report_type': 'tomorrow'}, name='detalle_tiempo_m'),
    path('tiempo/manana/<uuid:uuid>/pdf/', WeatherReportPDFView.as_view(), {'report_type': 'tomorrow'}, name='tiempo_m_pdf'),
    # Comentario Tiempo
    path('comentario/tiempo/', WeatherReportListView.as_view(), {'report_type': 'commentary'}, name='listado_comentarios_tiempo'),
    path('crear/comentario/tiempo/', WeatherReportCreateView.as_view(), {'report_type': 'commentary'}, name="crear_comentario_tiempo"),
    path('actualizar/comentario/tiempo/<uuid:uuid>/', WeatherReportUpdateView.as_view(), {'report_type': 'commentary'}, name='actualizar_comentario_tiempo'),
    path('eliminar/comentario/tiempo/<uuid:uuid>/', WeatherReportDeleteView.as_view(), {'report_type': 'commentary'}, name='eliminar_comentario_tiempo'),
    path('detalle/comentario/tiempo/<uuid:uuid>/', WeatherReportDetailView.as_view(), {'report_type': 'commentary'}, name='detalle_comentario_tiempo'),
    path('comentario/tiempo/<uuid:uuid>/pdf/', WeatherReportPDFView.as_view(), {'report_type': 'commentary'}, name='comentario_tiempo_pdf'),
    # Nota Meteorológica
    path('nota/meteorologica/', WeatherReportListView.as_view(), {'report_type': 'note'}, name='listado_notas_meteorologicas'),
    path('crear/nota/meteorologica/', WeatherReportCreateView.as_view(), {'report_type': 'note'}, name="crear_nota_meteorologica"),
    path('actualizar/nota/meteorologica/<uuid:uuid>/', WeatherReportUpdateView.as_view(), {'report_type': 'note'}, name='actualizar_nota_meteorologica'),
    path('eliminar/nota/meteorologica/<uuid:uuid>/', WeatherReportDeleteView.as_view(), {'report_type': 'note'}, name='eliminar_nota_meteorologica'),
    path('detalle/nota/meteorologica/<uuid:uuid>/', WeatherReportDetailView.as_view(), {'report_type': 'note'}, name='detalle_nota_meteorologica'),
    path('nota/meteorologica/<uuid:uuid>/pdf/', WeatherReportPDFView.as_view(), {'report_type': 'note'}, name='nota_meteorologica_pdf'),
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
