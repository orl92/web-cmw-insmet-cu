from django.urls import path

from apps.commercial.views.certificates import (
    CertificateCreateView,
    CertificateDeleteView,
    CertificateListView,
    CertificatePDFView,
)
from apps.commercial.views.contracts import (
    ContractCreateView,
    ContractDeleteView,
    ContractDetailView,
    ContractHardDeleteView,
    ContractListView,
)
from apps.commercial.views.customers import (
    CustomerCreateForUserView,
    CustomerCreateView,
    CustomerDeleteView,
    CustomerHardDeleteView,
    CustomerListView,
    CustomerUpdateView,
)
from apps.commercial.views.invoices import (
    CancelInvoiceView,
    InvoiceCreateView,
    InvoiceHardDeleteView,
    InvoiceListView,
    InvoicePDFDownloadView,
    ResendInvoiceEmailView,
    RetryInvoicePdfView,
    ajax_pending_subscriptions,
)
from apps.commercial.views.services import (
    ServiceCreateView,
    ServiceDeleteView,
    ServiceHardDeleteView,
    ServiceListView,
    ServicePDFDownloadView,
    ServiceReactivateView,
    ServiceUpdateView,
)
from apps.commercial.views.subscriptions import (
    ApproveSubscriptionView,
    CertificateHardDeleteView,
    RegenerateInvoiceView,
    ResendCertificateEmailView,
    SubscriptionCancelView,
    SubscriptionCreateView,
    SubscriptionHardDeleteView,
    SubscriptionListView,
    SubscriptionUpdateView,
)

app_name = 'commercial'

urlpatterns = [
    # Clientes
    path('clientes/', CustomerListView.as_view(), name='cliente_list'),
    path('crear/cliente/', CustomerCreateView.as_view(), name='cliente_create'),
    path(
        'crear/cliente/usuario/<uuid:user_uuid>/',
        CustomerCreateForUserView.as_view(),
        name='cliente_create_for_user',
    ),
    path('actualizar/cliente/<uuid:uuid>/', CustomerUpdateView.as_view(), name='cliente_update'),
    path('eliminar/cliente/<uuid:uuid>/', CustomerDeleteView.as_view(), name='cliente_delete'),
    path(
        'eliminar/cliente/<uuid:uuid>/permanente/',
        CustomerHardDeleteView.as_view(),
        name='cliente_hard_delete',
    ),
    # Servicios
    path('servicios/', ServiceListView.as_view(), name='servicio_list'),
    path('crear/servicios/', ServiceCreateView.as_view(), name='servicio_create'),
    path('actualizar/servicios/<uuid:uuid>/', ServiceUpdateView.as_view(), name='servicio_update'),
    path('eliminar/servicios/<uuid:uuid>/', ServiceDeleteView.as_view(), name='servicio_delete'),
    path(
        'reactivar/servicios/<uuid:uuid>/',
        ServiceReactivateView.as_view(),
        name='servicio_reactivate',
    ),
    path(
        'eliminar/servicios/<uuid:uuid>/permanente/',
        ServiceHardDeleteView.as_view(),
        name='servicio_hard_delete',
    ),
    path('servicios/<uuid:uuid>/pdf/', ServicePDFDownloadView.as_view(), name='servicio_pdf'),
    # Suscripciones
    path('suscripciones/', SubscriptionListView.as_view(), name='suscripcion_list'),
    path('crear/suscripcion/', SubscriptionCreateView.as_view(), name='suscripcion_create'),
    path(
        'actualizar/suscripcion/<uuid:uuid>/',
        SubscriptionUpdateView.as_view(),
        name='suscripcion_update',
    ),
    path(
        'anular/suscripcion/<uuid:uuid>/',
        SubscriptionCancelView.as_view(),
        name='suscripcion_cancel',
    ),
    path(
        'eliminar/suscripcion/<uuid:uuid>/',
        SubscriptionHardDeleteView.as_view(),
        name='suscripcion_delete',
    ),
    path(
        'regenerar-factura/<uuid:uuid>/', RegenerateInvoiceView.as_view(), name='factura_regenerate'
    ),
    path(
        'aprobar/suscripcion/<uuid:uuid>/',
        ApproveSubscriptionView.as_view(),
        name='suscripcion_approve',
    ),
    path(
        'reenviar/certificado/<uuid:uuid>/',
        ResendCertificateEmailView.as_view(),
        name='certificado_resend',
    ),
    # Certificados
    path('certificados/', CertificateListView.as_view(), name='certificado_list'),
    path('crear/certificado/', CertificateCreateView.as_view(), name='certificado_create'),
    path('certificado/<uuid:uuid>/pdf/', CertificatePDFView.as_view(), name='certificado_pdf'),
    path(
        'eliminar/certificado/<uuid:uuid>/',
        CertificateDeleteView.as_view(),
        name='certificado_delete',
    ),
    path(
        'eliminar/certificado/<uuid:uuid>/permanente/',
        CertificateHardDeleteView.as_view(),
        name='certificado_hard_delete',
    ),
    # Facturación
    path('facturacion/', InvoiceListView.as_view(), name='factura_list'),
    path('crear/factura/', InvoiceCreateView.as_view(), name='factura_create'),
    path('anular/factura/<uuid:uuid>/', CancelInvoiceView.as_view(), name='factura_cancel'),
    path('factura/<uuid:uuid>/pdf/', InvoicePDFDownloadView.as_view(), name='factura_download'),
    path('eliminar/factura/<uuid:uuid>/', InvoiceHardDeleteView.as_view(), name='factura_delete'),
    path(
        'reenviar/correo/factura/<uuid:uuid>/',
        ResendInvoiceEmailView.as_view(),
        name='factura_resend_email',
    ),
    path(
        'reintentar/pdf/factura/<uuid:uuid>/',
        RetryInvoicePdfView.as_view(),
        name='factura_retry_pdf',
    ),
    path(
        'ajax/suscripciones-pendientes/',
        ajax_pending_subscriptions,
        name='ajax_pending_subscriptions',
    ),
    # Contratos
    path('contratos/', ContractListView.as_view(), name='contrato_list'),
    path('crear/contrato/', ContractCreateView.as_view(), name='contrato_create'),
    path('detalle/contrato/<uuid:uuid>/', ContractDetailView.as_view(), name='contrato_detail'),
    path('eliminar/contrato/<uuid:uuid>/', ContractDeleteView.as_view(), name='contrato_delete'),
    path(
        'eliminar/contrato/<uuid:uuid>/permanente/',
        ContractHardDeleteView.as_view(),
        name='contrato_hard_delete',
    ),
]
