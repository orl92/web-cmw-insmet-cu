import json
import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, ListView, View

from common.utils import log_action
from dashboard.forms.company.forms import CompanySettingsForm
from dashboard.forms.facturacion.forms import InvoiceForm, InvoiceItemFormSet
from dashboard.models import (
    CompanySettings,
    Contract,
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from dashboard.tasks import generate_invoice_pdf_and_email_task
from dashboard.views.facturacion.utils import enviar_correo_factura

logger = logging.getLogger(__name__)


class InvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Invoice
    template_name = 'pages/dashboard/facturacion/listado_facturas.html'
    context_object_name = 'objects'
    paginate_by = 20
    permission_required = 'dashboard.view_invoice'

    def get_queryset(self):
        return Invoice.objects.select_related(
            'subscription__customer', 'subscription__service'
        ).prefetch_related('items').order_by('-issue_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Facturas'
        context['parent'] = 'facturacion'
        context['segment'] = 'facturas'
        context['btn'] = ('Añadir Factura')
        context['url_create'] = reverse_lazy('crear_factura')
        context['url_list'] = reverse_lazy('listado_facturas')
        context['url_export'] = reverse_lazy('exportar_csv_facturas')
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
        return context


class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'pages/dashboard/facturacion/crear_factura.html'
    form_class = InvoiceForm
    permission_required = 'dashboard.add_invoice'
    success_url = reverse_lazy('listado_facturas')

    def get_initial(self):
        initial = super().get_initial()
        today = timezone.now().date()
        customer_uuid = self.request.GET.get('customer_uuid')
        if customer_uuid:
            try:
                customer = Customer.objects.get(uuid=customer_uuid)
                initial['customer'] = customer
                pending_sub = ServiceSubscription.objects.filter(
                    customer=customer,
                    payment_status__in=['requested', 'pending'],
                    start_date__isnull=False,
                    end_date__isnull=False
                ).first()
                if pending_sub:
                    initial['start_date'] = pending_sub.start_date.date() if pending_sub.start_date else today
                    initial['end_date'] = pending_sub.end_date.date() if pending_sub.end_date else today + timedelta(days=30)
                else:
                    initial['start_date'] = today.isoformat()
                    initial['end_date'] = (today + timedelta(days=30)).isoformat()
            except Customer.DoesNotExist:
                pass
        else:
            initial['start_date'] = today.isoformat()
            initial['end_date'] = (today + timedelta(days=30)).isoformat()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Factura'
        context['parent'] = 'facturacion'
        context['segment'] = 'facturas'
        context['url_list'] = reverse_lazy('listado_facturas')
        context['items_formset'] = InvoiceItemFormSet(prefix='items')
        commercial_services = Service.objects.filter(service_type=Service.COMMERCIAL)
        context['commercial_services_json'] = json.dumps(
            list(commercial_services.values('id', 'code', 'title', 'price')),
            cls=DjangoJSONEncoder
        )
        context['company'] = CompanySettings.get_instance()
        return context

    def form_valid(self, form):
        customer = form.cleaned_data['customer']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        commercial_registry = form.cleaned_data['commercial_registry']
        subscriptions = form.cleaned_data.get('subscriptions')

        if subscriptions and subscriptions.exists():
            # Agrupar por período propio de cada suscripción
            groups = {}
            for sub in subscriptions:
                sub_start = sub.start_date.date() if sub.start_date else start_date
                sub_end = sub.end_date.date() if sub.end_date else end_date
                key = (sub_start, sub_end)
                groups.setdefault(key, []).append(sub)

            for (sub_start, sub_end), subs in groups.items():
                self.process_batch_invoice(customer, sub_start, sub_end, commercial_registry, subs)

            messages.success(self.request, f"Se generaron {len(groups)} factura(s) según los períodos de las suscripciones.")
            return redirect(self.success_url)
        else:
            return self.process_manual_invoice(form, customer, start_date, end_date, commercial_registry)

    def process_batch_invoice(self, customer, start_date, end_date, commercial_registry, subscriptions):
        days_count = (end_date - start_date).days
        invoice = Invoice.objects.create(
            subscription=None,
            customer=customer,
            amount=0,
            number=self.generate_invoice_number()
        )
        total = 0
        items = []
        for sub in subscriptions:
            price = sub.service.price or 0
            amount = price * days_count
            item = InvoiceItem.objects.create(
                invoice=invoice,
                subscription=sub,
                codigo=sub.service.code or '',
                descripcion=sub.service.title,
                cantidad=days_count,
                precio=price,
                importe=amount,
            )
            items.append(item)
            total += amount

            # Actualizar suscripción con las fechas del grupo
            sub.start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            sub.end_date = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
            sub.payment_status = 'pending'
            sub.save()

            # Contrato
            contract, created = Contract.objects.get_or_create(
                subscription=sub,
                defaults={
                    'number': self.generate_contract_number(),
                    'date': timezone.now().date(),
                    'commercial_registry': commercial_registry,
                }
            )
            if not created:
                contract.commercial_registry = commercial_registry
                contract.save(update_fields=['commercial_registry'])

            log_action(
                user=self.request.user,
                obj=sub,
                action_flag=CHANGE,
                message=f"Suscripción facturada en lote: {sub.service.title} para {sub.customer.company_name}"
            )

        invoice.amount = total
        invoice.save()

        log_action(
            user=self.request.user,
            obj=invoice,
            action_flag=ADDITION,
            message=f"Factura por lote {invoice.number} - Cliente: {customer.company_name} - Monto: ${total:.2f}"
        )

        site_url = self.request.build_absolute_uri('/')
        generate_invoice_pdf_and_email_task(str(invoice.uuid), site_url)

    def process_manual_invoice(self, form, customer, start_date, end_date, commercial_registry):
        items_formset = InvoiceItemFormSet(self.request.POST, prefix='items')
        if not items_formset.is_valid():
            messages.error(self.request, "Corrige los errores en las líneas de factura.")
            context = self.get_context_data(form=form)
            context['items_formset'] = items_formset
            return self.render_to_response(context)

        days_count = (end_date - start_date).days

        invoice = Invoice.objects.create(
            subscription=None,
            customer=customer,
            amount=0,
            number=self.generate_invoice_number()
        )
        total = 0
        items = []
        first_sub = None

        for item_form in items_formset:
            if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                cd = item_form.cleaned_data
                service = cd['service']

                sub = ServiceSubscription.objects.create(
                    customer=customer,
                    service=service,
                    start_date=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
                    end_date=timezone.make_aware(datetime.combine(end_date, datetime.min.time())),
                    payment_status='pending',
                    record_active=True
                )

                if first_sub is None:
                    first_sub = sub

                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    subscription=sub,
                    codigo=cd.get('codigo', service.code or ''),
                    descripcion=service.title,
                    cantidad=days_count,
                    unidad_medida=cd.get('unidad_medida', 'U'),
                    precio=cd['precio'],
                    importe=days_count * cd['precio'],
                )
                items.append(item)
                total += days_count * cd['precio']

                log_action(
                    user=self.request.user,
                    obj=sub,
                    action_flag=ADDITION,
                    message=f"Suscripción creada manualmente: {customer.company_name} - {service.title}"
                )

        invoice.amount = total
        if first_sub:
            invoice.subscription = first_sub
        invoice.save()

        log_action(
            user=self.request.user,
            obj=invoice,
            action_flag=ADDITION,
            message=f"Factura manual {invoice.number} - Cliente: {customer.company_name} - Monto: ${total:.2f}"
        )

        site_url = self.request.build_absolute_uri('/')
        generate_invoice_pdf_and_email_task(str(invoice.uuid), site_url)
        messages.success(self.request, "Factura manual generada (con suscripciones creadas).")
        return redirect(self.success_url)

    def generate_invoice_number(self):
        year = timezone.now().year
        last = Invoice.objects.filter(issue_date__year=year).order_by('-issue_date').first()
        if last and last.number:
            try:
                num = int(last.number.split('-')[-1])
                return f"{year}-{num+1:04d}"
            except (ValueError, IndexError):
                pass
        return f"{year}-0001"

    def generate_contract_number(self):
        year = timezone.now().year
        last_contract = Contract.objects.filter(date__year=year).order_by('-date').first()
        if last_contract and last_contract.number:
            try:
                num = int(last_contract.number.split('-')[-1])
                return f"{year}-{num+1:04d}"
            except (ValueError, IndexError):
                pass
        return f"{year}-0001"


class CancelInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_invoice'

    def post(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)

        if invoice.is_cancelled:
            messages.warning(request, f"La factura {invoice.number} ya estaba anulada.")
            return redirect('listado_facturas')

        invoice.is_cancelled = True
        invoice.save()

        items_with_subs = invoice.items.filter(subscription__isnull=False).select_related('subscription')
        for item in items_with_subs:
            sub = item.subscription
            if sub.payment_status in ['pending', 'requested']:
                sub.payment_status = 'requested'
                sub.save()
                log_action(
                    user=request.user,
                    obj=sub,
                    action_flag=CHANGE,
                    message=f"Estado revertido a 'solicitado' por anulación de factura {invoice.number}"
                )

        log_action(
            user=request.user,
            obj=invoice,
            action_flag=CHANGE,
            message=f"Factura {invoice.number} anulada"
        )
        messages.success(request, f"Factura {invoice.number} anulada correctamente.")
        return redirect('listado_facturas')


class InvoiceHardDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)
        invoice_number = invoice.number
        log_action(
            user=request.user,
            obj=invoice,
            action_flag=DELETION,
            message=f"Factura {invoice.number} eliminada permanentemente"
        )
        invoice.hard_delete()
        messages.success(request, f"Factura {invoice_number} eliminada permanentemente.")
        return redirect('listado_facturas')


class ResendInvoiceEmailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.change_invoice'

    def get(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)

        customer = None
        if invoice.subscription:
            customer = invoice.subscription.customer
        elif invoice.customer:
            customer = invoice.customer
        else:
            first_item = invoice.items.first()
            if first_item and first_item.subscription:
                customer = first_item.subscription.customer

        if not customer or not customer.user or not customer.user.email:
            messages.error(request, "No se pudo determinar el cliente o no tiene correo electrónico.")
            return redirect('listado_facturas')

        exito = enviar_correo_factura(invoice, customer, request=request)
        if exito:
            messages.success(request, f"Correo de la factura {invoice.number} reenviado correctamente.")
        else:
            messages.error(request, f"No se pudo reenviar el correo de la factura {invoice.number}. Revise los logs.")
        return redirect('listado_facturas')


def ajax_pending_subscriptions(request):
    customer_id = request.GET.get('customer')
    if not customer_id:
        return HttpResponse('')
    subs = ServiceSubscription.objects.filter(
        customer_id=customer_id,
        payment_status__in=['requested', 'pending'],
        record_active=True
    ).select_related('service')
    if not subs.exists():
        return HttpResponse('<p class="text-muted">No hay suscripciones pendientes.</p>')
    html = ''
    for sub in subs:
        start_str = sub.start_date.strftime('%Y-%m-%d') if sub.start_date else ''
        end_str = sub.end_date.strftime('%Y-%m-%d') if sub.end_date else ''
        days = (sub.end_date - sub.start_date).days if sub.start_date and sub.end_date else 0
        summary = sub.service.summary or ''
        html += f'''
        <div class="form-check">
          <input class="form-check-input subscription-check" type="checkbox" name="subscriptions" value="{sub.pk}" 
                 id="sub_{sub.pk}" data-start="{start_str}" data-end="{end_str}" 
                 data-service="{sub.service.title}" data-days="{days}" data-summary="{summary}">
          <label class="form-check-label" for="sub_{sub.pk}">
            <strong>{sub.service.title}</strong>
            <br><small class="text-muted">{summary}</small>
          </label>
        </div>
        '''
    return HttpResponse(html)


class ContractHardDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Eliminación física de contrato (solo superusuarios)."""
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, uuid):
        contract = get_object_or_404(Contract, uuid=uuid)
        contract_number = contract.number
        contract.hard_delete()
        log_action(
            user=request.user,
            obj=contract,
            action_flag=DELETION,
            message=f"Contrato {contract_number} eliminado físicamente."
        )
        messages.success(request, f"Contrato {contract_number} eliminado permanentemente.")
        return redirect('listado_suscripciones')


class CompanySettingsAjaxUpdateView(View):
    def post(self, request, *args, **kwargs):
        instance = CompanySettings.get_instance()
        form = CompanySettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
