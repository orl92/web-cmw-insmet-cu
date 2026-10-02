import csv
import json

from django.contrib.admin.models import CHANGE, DELETION
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.views import View

from apps.commercial.models import Certificate, Customer, Invoice, ServiceSubscription
from apps.commercial.views.exports import (
    CertificateCSVExportView,
    CustomerCSVExportView,
    InvoiceCSVExportView,
    ServiceSubscriptionCSVExportView,
)
from apps.core.utils import log_action
from apps.core.views.exports import _resolve


class BulkActionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Base view for bulk operations on a model.

    Accepts POST with JSON body:
    {"action": "export"|"delete"|"update",
     "uuids": [uuid, ...], "field"?: str, "value"?: str}
    """

    model = None
    permission_required_map = {
        'export': None,
        'delete': None,
        'update': None,
    }
    csv_export_view_class = None
    update_allowlist = {}

    def get_permission_required(self):
        action = self._get_action_from_body()
        perm = self.permission_required_map.get(action)
        if perm:
            return [perm]
        return []

    def _get_action_from_body(self):
        try:
            body = json.loads(self.request.body)
        except json.JSONDecodeError, ValueError, TypeError:
            return None
        return body.get('action')

    @transaction.atomic
    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError, ValueError:
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        action = body.get('action')
        uuids = body.get('uuids', [])

        if action not in ('export', 'delete', 'update'):
            return JsonResponse({'error': f'Unknown action: {action}'}, status=400)

        if not uuids or not isinstance(uuids, list):
            return JsonResponse(
                {'error': 'uuids list is required and must not be empty'},
                status=400,
            )

        uuids = [str(u) for u in uuids]

        if action == 'export':
            return self._handle_export(request, uuids)
        if action == 'delete':
            return self._handle_delete(request, uuids)
        if action == 'update':
            return self._handle_update(request, body, uuids)

        return JsonResponse({'error': 'Unknown action'}, status=400)

    def _handle_export(self, request, uuids):
        export_view_cls = self.csv_export_view_class
        qs = self.model.objects.filter(uuid__in=uuids)
        columns = export_view_cls.columns
        filename = export_view_cls.filename

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow([h for h, _ in columns])
        for obj in qs:
            row = [_resolve(v, obj) for _, v in columns]
            writer.writerow(row)
        return response

    def _handle_delete(self, request, uuids):
        qs = self.model.objects.filter(uuid__in=uuids, record_active=True)
        processed = 0
        total = len(uuids)
        first_obj = qs.first()

        for obj in qs:
            obj.delete()
            processed += 1

        if processed and first_obj:
            log_action(
                user=request.user,
                obj=first_obj,
                action_flag=DELETION,
                message=(
                    f'{processed} {self.model._meta.verbose_name}(s) '
                    f'desactivado(s) por acción masiva'
                ),
                request=request,
            )

        return JsonResponse(
            {
                'status': 'ok',
                'processed': processed,
                'skipped': max(0, total - processed),
            }
        )

    def validate_update(self, qs, field, value):
        """Invariantes que la acción masiva no puede violar.

        Recibe los objetos ya filtrados (uuid + `record_active`) y devuelve el
        mensaje de error, o `None` si el cambio se puede aplicar a todos. Se
        llama una sola vez, antes de cualquier `save`, para que un rechazo no
        deje registros a medio actualizar.
        """
        return None

    def _handle_update(self, request, body, uuids):
        field = body.get('field', '')
        value = body.get('value', '')

        if field not in self.update_allowlist:
            return JsonResponse(
                {'error': f'Field "{field}" is not in the allow-list'},
                status=400,
            )

        valid_values = self.update_allowlist[field]
        if valid_values and value not in valid_values:
            return JsonResponse(
                {'error': f'Invalid value "{value}" for field "{field}"'},
                status=400,
            )

        qs = self.model.objects.filter(uuid__in=uuids, record_active=True)
        processed = 0
        total = len(uuids)
        first_obj = qs.first()

        # Se valida antes de tocar nada: una acción masiva que aplicara el cambio
        # a los válidos y dejara fuera a los inválidos deja estados a medias que
        # nadie pidió y que hay que corregir a mano.
        error = self.validate_update(qs, field, value)
        if error:
            return JsonResponse(
                {'error': error, 'processed': 0, 'skipped': len(qs)},
                status=400,
            )

        for obj in qs:
            setattr(obj, field, value)
            obj.save(update_fields=[field])
            processed += 1

        if processed and first_obj:
            log_action(
                user=request.user,
                obj=first_obj,
                action_flag=CHANGE,
                message=(
                    f'{processed} {self.model._meta.verbose_name}(s) '
                    f'actualizado(s) por acción masiva: {field} → {value}'
                ),
                request=request,
            )

        return JsonResponse(
            {
                'status': 'ok',
                'processed': processed,
                'skipped': max(0, total - processed),
            }
        )


class CustomerBulkActionView(BulkActionView):
    model = Customer
    permission_required_map = {
        'export': 'commercial.view_customer',
        'delete': 'commercial.delete_customer',
        'update': 'commercial.change_customer',
    }
    csv_export_view_class = CustomerCSVExportView
    update_allowlist = {}


class ServiceSubscriptionBulkActionView(BulkActionView):
    model = ServiceSubscription
    permission_required_map = {
        'export': 'commercial.view_subscription',
        'delete': 'commercial.delete_subscription',
        'update': 'commercial.change_subscription',
    }
    csv_export_view_class = ServiceSubscriptionCSVExportView
    update_allowlist = {
        'payment_status': ['requested', 'pending', 'paid'],
    }

    def validate_update(self, qs, field, value):
        error = super().validate_update(qs, field, value)
        if error:
            return error
        if field != 'payment_status' or value != 'paid':
            return None
        # Pagado sin certificado es el estado que reportaba el operador: la
        # factura aparece pagada y no hay ningún documento que la respalde.
        # La acción masiva no sube certificados, así que aquí sólo puede
        # rechazar; el camino que sí los sube es `ApproveSubscriptionView`.
        con_certificado = set(
            qs.filter(certificates__record_active=True)
            .exclude(certificates__pdf='')
            .values_list('uuid', flat=True)
            .distinct()
        )
        sin_certificado = list(qs.exclude(uuid__in=con_certificado).values_list('uuid', flat=True))
        if sin_certificado:
            return (
                f'No se puede marcar como pagada {len(sin_certificado)} suscripción(es) '
                'sin certificado: el pago se aprueba subiendo el certificado desde la '
                'suscripción.'
            )
        return None


class InvoiceBulkActionView(BulkActionView):
    model = Invoice
    permission_required_map = {
        'export': 'commercial.view_invoice',
        'delete': 'commercial.delete_invoice',
        'update': 'commercial.change_invoice',
    }
    csv_export_view_class = InvoiceCSVExportView
    update_allowlist = {}


class CertificateBulkActionView(BulkActionView):
    model = Certificate
    permission_required_map = {
        'export': 'commercial.view_certificate',
        'delete': 'commercial.delete_certificate',
        'update': 'commercial.change_certificate',
    }
    csv_export_view_class = CertificateCSVExportView
    update_allowlist = {}
