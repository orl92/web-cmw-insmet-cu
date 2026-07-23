from django.urls import include, path, reverse_lazy
from django.views.generic.base import RedirectView

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

from apps.dashboard.views.avisos.alertas_tempranas.views import (
    EarlyWarningCreateView,
    EarlyWarningDeleteView,
    EarlyWarningListView,
    EarlyWarningUpdateView,
)
from apps.dashboard.views.avisos.ciclones_tropicales.views import (
    TropicalCycloneCreateView,
    TropicalCycloneDeleteView,
    TropicalCycloneListView,
    TropicalCycloneUpdateView,
)
from apps.dashboard.views.avisos.tormentas.views import (
    StormWarningCreateView,
    StormWarningDeleteView,
    StormWarningListView,
    StormWarningUpdateView,
)
from apps.dashboard.views.certificados.views import (
    CertificateCreateView,
    CertificateDeleteView,
    CertificateDetailView,
    CertificateListView,
    CertificatePDFView,
)
from apps.dashboard.views.clientes.views import (
    CustomerCreateForUserView,
    CustomerCreateView,
    CustomerDeleteView,
    CustomerHardDeleteView,
    CustomerListView,
    CustomerUpdateView,
)
from apps.dashboard.views.contratos.views import (
    ContractCreateView,
    ContractDeleteView,
    ContractDetailView,
    ContractListView,
)
from apps.dashboard.views.company.views import CompanySettingsUpdateView
from apps.dashboard.views.dashboard.dashboard import DashboardView
from apps.dashboard.views.dashboard.excel_json import ExcelJSONView
from apps.dashboard.views.dashboard.maintenance import MaintenanceModeToggleView
from apps.dashboard.views.exports import (
    CertificateCSVExportView,
    ContractCSVExportView,
    CustomerCSVExportView,
    EmailRecipientListCSVExportView,
    ForecastsCSVExportView,
    ForecastsExcelExportView,
    InvoiceCSVExportView,
    ServiceCSVExportView,
    ServiceSubscriptionCSVExportView,
)
from apps.dashboard.views.email_recipient.views import (
    EmailRecipientListCreateView,
    EmailRecipientListDeleteView,
    EmailRecipientListListView,
    EmailRecipientListUpdateView,
)
from apps.dashboard.views.facturacion.views import (
    CancelInvoiceView,
    CompanySettingsAjaxUpdateView,
    ContractHardDeleteView,
    InvoiceCreateView,
    InvoiceHardDeleteView,
    InvoiceListView,
    ResendInvoiceEmailView,
    ajax_pending_subscriptions,
)
from apps.dashboard.views.pronosticos.views import (
    AllForecastCreateView,
    ForecastDeleteView,
    ForecastsListView,
    ForecastUpdateView,
)
from apps.dashboard.views.servicios.views import (
    ServiceCreateView,
    ServiceDeleteView,
    ServiceHardDeleteView,
    ServiceListView,
    ServiceUpdateView,
)
from apps.dashboard.views.suscripciones.views import (
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
from apps.dashboard.views.tiempo.views import (
    WeatherReportCreateView,
    WeatherReportDeleteView,
    WeatherReportDetailView,
    WeatherReportListView,
    WeatherReportPDFView,
    WeatherReportUpdateView,
)

app_name = 'dashboard'

urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name="index"),
    path('', include('apps.geo.urls')),
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
    # Pronósticos
    path('pronosticos/', ForecastsListView.as_view(), name='pronostico_list'),
    path('crear/pronostico/', AllForecastCreateView.as_view(), name='pronostico_create'),
    path('actualizar/pronostico/<uuid:uuid>/', ForecastUpdateView.as_view(), name='pronostico_update'),
    path('eliminar/pronostico/<uuid:uuid>/', ForecastDeleteView.as_view(), name='pronostico_delete'),
    # Excel json
    path('excel/json/', ExcelJSONView.as_view(), name='excel_json'),
    # Aviso Alerta Temprana
    path('avisos/alertas_tempranas/', EarlyWarningListView.as_view(), name='alerta_temprana_list'),
    path('crear/aviso/alerta_temprana/', EarlyWarningCreateView.as_view(), name="alerta_temprana_create"),
    path('actualizar/aviso/alerta_temprana/<uuid:uuid>/', EarlyWarningUpdateView.as_view(), name='alerta_temprana_update'),
    path('eliminar/aviso/alerta_temprana/<uuid:uuid>/', EarlyWarningDeleteView.as_view(), name='alerta_temprana_delete'),
    # Aviso Ciclón Tropical
    path('avisos/ciclones_tropicales/', TropicalCycloneListView.as_view(), name='ciclon_tropical_list'),
    path('crear/aviso/ciclon_tropical/', TropicalCycloneCreateView.as_view(), name="ciclon_tropical_create"),
    path('actualizar/aviso/ciclon_tropical/<uuid:uuid>/', TropicalCycloneUpdateView.as_view(), name='ciclon_tropical_update'),
    path('eliminar/aviso/ciclon_tropical/<uuid:uuid>/', TropicalCycloneDeleteView.as_view(), name='ciclon_tropical_delete'),
    # Aviso Tormenta
    path('avisos/tormentas/', StormWarningListView.as_view(), name='tormenta_list'),
    path('crear/aviso/tormenta/', StormWarningCreateView.as_view(), name="tormenta_create"),
    path('actualizar/aviso/tormenta/<uuid:uuid>/', StormWarningUpdateView.as_view(), name='tormenta_update'),
    path('eliminar/aviso/tormenta/<uuid:uuid>/', StormWarningDeleteView.as_view(), name='tormenta_delete'),
    # Clientes
    path('clientes/', CustomerListView.as_view(), name='cliente_list'),
    path('crear/cliente/', CustomerCreateView.as_view(), name='cliente_create'),
    path('crear/cliente/usuario/<uuid:user_uuid>/', CustomerCreateForUserView.as_view(), name='cliente_create_for_user'),
    path('actualizar/cliente/<uuid:uuid>/', CustomerUpdateView.as_view(), name='cliente_update'),
    path('eliminar/cliente/<uuid:uuid>/', CustomerDeleteView.as_view(), name='cliente_delete'),
    path('eliminar/cliente/<uuid:uuid>/permanente/', CustomerHardDeleteView.as_view(), name='cliente_hard_delete'),
    path('clientes/exportar/csv/', CustomerCSVExportView.as_view(), name='cliente_export_csv'),
    # Servicios
    path('servicios/', ServiceListView.as_view(), name='servicio_list'),
    path('crear/servicios/', ServiceCreateView.as_view(), name='servicio_create'),
    path('actualizar/servicios/<uuid:uuid>/', ServiceUpdateView.as_view(), name='servicio_update'),
    path('eliminar/servicios/<uuid:uuid>/', ServiceDeleteView.as_view(), name='servicio_delete'),
    path('eliminar/servicios/<uuid:uuid>/permanente/', ServiceHardDeleteView.as_view(), name='servicio_hard_delete'),
    path('servicios/exportar/csv/', ServiceCSVExportView.as_view(), name='servicio_export_csv'),
    # Suscripciones
    path('suscripciones/', SubscriptionListView.as_view(), name='suscripcion_list'),
    path('crear/suscripcion/', SubscriptionCreateView.as_view(), name='suscripcion_create'),
    path('actualizar/suscripcion/<uuid:uuid>/', SubscriptionUpdateView.as_view(), name='suscripcion_update'),
    path('anular/suscripcion/<uuid:uuid>/', SubscriptionCancelView.as_view(), name='suscripcion_cancel'),
    path('eliminar/suscripcion/<uuid:uuid>/', SubscriptionHardDeleteView.as_view(), name='suscripcion_delete'),
    path('renovar/suscripcion/<uuid:uuid>/', SubscriptionRenewView.as_view(), name='suscripcion_renew'),
    path('regenerar-factura/<uuid:uuid>/', RegenerateInvoiceView.as_view(), name='factura_regenerate'),
    path('aprobar/suscripcion/<uuid:uuid>/', ApproveSubscriptionView.as_view(), name='suscripcion_approve'),
    path('reenviar/certificado/<uuid:uuid>/', ResendCertificateEmailView.as_view(), name='certificado_resend'),
    # Certificados
    path('certificados/', CertificateListView.as_view(), name='certificado_list'),
    path('crear/certificado/', CertificateCreateView.as_view(), name='certificado_create'),
    path('detalle/certificado/<uuid:uuid>/', CertificateDetailView.as_view(), name='certificado_detail'),
    path('certificado/<uuid:uuid>/pdf/', CertificatePDFView.as_view(), name='certificado_pdf'),
    path('eliminar/certificado/<uuid:uuid>/', CertificateDeleteView.as_view(), name='certificado_delete'),
    path('eliminar/certificado/<uuid:uuid>/permanente/', CertificateHardDeleteView.as_view(), name='certificado_hard_delete'),
    path('suscripciones/exportar/csv/', ServiceSubscriptionCSVExportView.as_view(), name='suscripcion_export_csv'),
    # Facturación
    path('facturacion/', InvoiceListView.as_view(), name='factura_list'),
    path('crear/factura/', InvoiceCreateView.as_view(), name='factura_create'),
    path('anular/factura/<uuid:uuid>/', CancelInvoiceView.as_view(), name='factura_cancel'),
    path('eliminar/factura/<uuid:uuid>/', InvoiceHardDeleteView.as_view(), name='factura_delete'),
    path('reenviar/correo/factura/<uuid:uuid>/', ResendInvoiceEmailView.as_view(), name='factura_resend_email'),
    path('ajax/suscripciones-pendientes/', ajax_pending_subscriptions, name='ajax_pending_subscriptions'),
    # Contratos
    path('contratos/', ContractListView.as_view(), name='contrato_list'),
    path('crear/contrato/', ContractCreateView.as_view(), name='contrato_create'),
    path('detalle/contrato/<uuid:uuid>/', ContractDetailView.as_view(), name='contrato_detail'),
    path('eliminar/contrato/<uuid:uuid>/', ContractDeleteView.as_view(), name='contrato_delete'),
    path('eliminar/contrato/<uuid:uuid>/permanente/', ContractHardDeleteView.as_view(), name='contrato_hard_delete'),
    path('facturacion/exportar/csv/', InvoiceCSVExportView.as_view(), name='factura_export_csv'),
    path('pronosticos/exportar/csv/', ForecastsCSVExportView.as_view(), name='pronostico_export_csv'),
    path('pronosticos/exportar/excel/', ForecastsExcelExportView.as_view(), name='pronostico_export_excel'),
    path('contratos/exportar/csv/', ContractCSVExportView.as_view(), name='contrato_export_csv'),
    path('certificados/exportar/csv/', CertificateCSVExportView.as_view(), name='certificado_export_csv'),
    path('listas-correo/exportar/csv/', EmailRecipientListCSVExportView.as_view(), name='lista_correo_export_csv'),
    # Tiempo Hoy
    path('tiempo/hoy/', WeatherReportListView.as_view(), {'report_type': 'today'}, name='tiempo_hoy_list'),
    path('crear/tiempo/hoy/', WeatherReportCreateView.as_view(), {'report_type': 'today'}, name="tiempo_hoy_create"),
    path('actualizar/tiempo/hoy/<uuid:uuid>/', WeatherReportUpdateView.as_view(), {'report_type': 'today'}, name='tiempo_hoy_update'),
    path('eliminar/tiempo/hoy/<uuid:uuid>/', WeatherReportDeleteView.as_view(), {'report_type': 'today'}, name='tiempo_hoy_delete'),
    path('detalle/tiempo/hoy/<uuid:uuid>/', WeatherReportDetailView.as_view(), {'report_type': 'today'}, name='tiempo_hoy_detail'),
    path('tiempo/hoy/<uuid:uuid>/pdf/', WeatherReportPDFView.as_view(), {'report_type': 'today'}, name='tiempo_hoy_pdf'),
    # Tiempo Mañana
    path('tiempo/manana/', WeatherReportListView.as_view(), {'report_type': 'tomorrow'}, name='tiempo_manana_list'),
    path('crear/tiempo/manana/', WeatherReportCreateView.as_view(), {'report_type': 'tomorrow'}, name="tiempo_manana_create"),
    path('actualizar/tiempo/manana/<uuid:uuid>/', WeatherReportUpdateView.as_view(), {'report_type': 'tomorrow'}, name='tiempo_manana_update'),
    path('eliminar/tiempo/manana/<uuid:uuid>/', WeatherReportDeleteView.as_view(), {'report_type': 'tomorrow'}, name='tiempo_manana_delete'),
    path('detalle/tiempo/manana/<uuid:uuid>/', WeatherReportDetailView.as_view(), {'report_type': 'tomorrow'}, name='tiempo_manana_detail'),
    path('tiempo/manana/<uuid:uuid>/pdf/', WeatherReportPDFView.as_view(), {'report_type': 'tomorrow'}, name='tiempo_manana_pdf'),
    # Comentario Tiempo
    path('comentario/tiempo/', WeatherReportListView.as_view(), {'report_type': 'commentary'}, name='comentario_tiempo_list'),
    path('crear/comentario/tiempo/', WeatherReportCreateView.as_view(), {'report_type': 'commentary'}, name="comentario_tiempo_create"),
    path('actualizar/comentario/tiempo/<uuid:uuid>/', WeatherReportUpdateView.as_view(), {'report_type': 'commentary'}, name='comentario_tiempo_update'),
    path('eliminar/comentario/tiempo/<uuid:uuid>/', WeatherReportDeleteView.as_view(), {'report_type': 'commentary'}, name='comentario_tiempo_delete'),
    path('detalle/comentario/tiempo/<uuid:uuid>/', WeatherReportDetailView.as_view(), {'report_type': 'commentary'}, name='comentario_tiempo_detail'),
    path('comentario/tiempo/<uuid:uuid>/pdf/', WeatherReportPDFView.as_view(), {'report_type': 'commentary'}, name='comentario_tiempo_pdf'),
    # Nota Meteorológica
    path('nota/meteorologica/', WeatherReportListView.as_view(), {'report_type': 'note'}, name='nota_meteorologica_list'),
    path('crear/nota/meteorologica/', WeatherReportCreateView.as_view(), {'report_type': 'note'}, name="nota_meteorologica_create"),
    path('actualizar/nota/meteorologica/<uuid:uuid>/', WeatherReportUpdateView.as_view(), {'report_type': 'note'}, name='nota_meteorologica_update'),
    path('eliminar/nota/meteorologica/<uuid:uuid>/', WeatherReportDeleteView.as_view(), {'report_type': 'note'}, name='nota_meteorologica_delete'),
    path('detalle/nota/meteorologica/<uuid:uuid>/', WeatherReportDetailView.as_view(), {'report_type': 'note'}, name='nota_meteorologica_detail'),
    path('nota/meteorologica/<uuid:uuid>/pdf/', WeatherReportPDFView.as_view(), {'report_type': 'note'}, name='nota_meteorologica_pdf'),
    # Listado de Correos
    path('listado/correos/', EmailRecipientListListView.as_view(), name='lista_correo_list'),
    path('crear/listado/correo/', EmailRecipientListCreateView.as_view(), name='lista_correo_create'),
    path('actualizar/listado/correo/<uuid:uuid>/', EmailRecipientListUpdateView.as_view(), name='lista_correo_update'),
    path('eliminar/listado/correo/<uuid:uuid>/', EmailRecipientListDeleteView.as_view(), name='lista_correo_delete'),
    # Configuracion Empresa
    path('configuracion/empresa/', CompanySettingsUpdateView.as_view(), name='company_settings'),
    path('configuracion/empresa/ajax/', CompanySettingsAjaxUpdateView.as_view(), name='company_settings_ajax'),
    # Modo Mantenimiento
    path('toggle-maintenance/', MaintenanceModeToggleView.as_view(), name='toggle_maintenance_mode'),
]
