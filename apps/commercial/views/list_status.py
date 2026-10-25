"""Endpoints AJAX de estado en vivo para los listados de facturación.

Devuelven JSON con el fragmento ya renderizado de las celdas Estado y Acciones
de cada fila, para que el JS de `list-live-status.js` las reemplace sin
redibujar DataTables ni recargar la página. La fuente de verdad del markup son
los mismos partials que usan los listados.
"""

import uuid

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.template.loader import render_to_string

from apps.commercial.models import Invoice, InvoiceItem
from apps.commercial.views.subscriptions import queryset_de_suscripciones_con_estado

MAX_UUIDS = 500


def _uuids_consultados(request):
    """UUIDs válidos y únicos del query param `?uuids=`, con tope razonable.

    Un valor malformado no es un error del servidor: el cliente apenas armó
    mal la lista, así que se ignora en vez de responder 500.
    """
    raw = request.GET.get('uuids', '')
    vistos = set()
    for parte in raw.split(','):
        parte = parte.strip()
        if not parte:
            continue
        try:
            valor = uuid.UUID(parte)
        except AttributeError, TypeError, ValueError:
            continue
        vistos.add(valor)
        if len(vistos) >= MAX_UUIDS:
            break
    return vistos


@login_required
@permission_required('commercial.view_invoice')
def ajax_invoice_status(request):
    facturas = (
        Invoice.objects.select_related(
            'customer__user', 'subscription__customer__user', 'subscription__service'
        )
        .prefetch_related(
            # El desglose de la celda Estado lee la suscripción y su servicio de
            # cada línea: el `select_related` del prefetch evita una consulta por
            # línea (mismo N+1 que el listado).
            Prefetch(
                'items',
                queryset=InvoiceItem.objects.select_related('subscription__service'),
            )
        )
        .with_display_status()
        .filter(uuid__in=_uuids_consultados(request))
    )
    rows = []
    pending = False
    for factura in facturas:
        fila_pendiente = (
            factura.pdf_status == factura.PdfStatus.PENDING
            or factura.email_status == factura.EmailStatus.PENDING
        )
        pending = pending or fila_pendiente
        rows.append(
            {
                'uuid': str(factura.uuid),
                'status_html': render_to_string(
                    'includes/commercial/invoice/status_cell.html',
                    {'invoice': factura},
                    request=request,
                ),
                'actions_html': render_to_string(
                    'includes/commercial/invoice/actions_cell.html',
                    {'invoice': factura, 'is_superuser': request.user.is_superuser},
                    request=request,
                ),
                'pending': fila_pendiente,
            }
        )
    return JsonResponse({'rows': rows, 'pending': pending})


@login_required
@permission_required('commercial.view_subscription')
def ajax_subscription_status(request):
    # Mismo filtro por rol que `SubscriptionListView`: un usuario del grupo
    # `Clientes` nunca recibe estado de suscripciones ajenas.
    suscripciones = queryset_de_suscripciones_con_estado(request.user).filter(
        uuid__in=_uuids_consultados(request)
    )
    rows = []
    pending = False
    for sub in suscripciones:
        # Sin factura no hay nada asíncrono que esperar: si exigiéramos sólo
        # `not latest_invoice_pdf_ready`, una suscripción pendiente cuya factura
        # se anuló mantendría el polling vivo para siempre (el PDF nunca llega).
        fila_pendiente = (
            sub.payment_status == 'pending'
            and sub.latest_invoice_uuid is not None
            and not sub.latest_invoice_pdf_ready
        )
        pending = pending or fila_pendiente
        rows.append(
            {
                'uuid': str(sub.uuid),
                'status_html': render_to_string(
                    'includes/commercial/subscription/status_cell.html',
                    {'subscription': sub},
                    request=request,
                ),
                'actions_html': render_to_string(
                    'includes/commercial/subscription/actions_cell.html',
                    {'subscription': sub, 'is_superuser': request.user.is_superuser},
                    request=request,
                ),
                'pending': fila_pendiente,
            }
        )
    return JsonResponse({'rows': rows, 'pending': pending})
