import json
import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from django.views.generic import FormView, ListView, View

from apps.commercial.forms.invoice import InvoiceForm, InvoiceItemFormSet
from apps.commercial.models import (
    Contract,
    Customer,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.views.invoice_utils import enviar_correo_factura
from apps.core.models import CompanySettings
from apps.core.tasks import generate_invoice_pdf_and_email_task
from apps.core.utils import log_action
from apps.core.views import ServeModelFileView

logger = logging.getLogger(__name__)


class InvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Invoice
    template_name = 'pages/commercial/invoice/list.html'
    context_object_name = 'objects'
    permission_required = 'commercial.view_invoice'

    def get_queryset(self):
        return (
            Invoice.objects.select_related('subscription__customer', 'subscription__service')
            .prefetch_related('items')
            .order_by('-issue_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Facturas'
        context['parent'] = 'facturacion'
        context['segment'] = 'facturas'
        context['btn'] = 'Añadir Factura'
        context['url_create'] = reverse_lazy('commercial:factura_create')
        context['url_list'] = reverse_lazy('commercial:factura_list')
        context['url_export'] = reverse_lazy('commercial:factura_export_csv')
        context['is_superuser'] = self.request.user.is_superuser
        return context


class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'pages/commercial/invoice/create.html'
    form_class = InvoiceForm
    permission_required = 'commercial.add_invoice'
    success_url = reverse_lazy('commercial:factura_list')

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
                    end_date__isnull=False,
                ).first()
                if pending_sub:
                    initial['start_date'] = (
                        pending_sub.start_date.date() if pending_sub.start_date else today
                    )
                    initial['end_date'] = (
                        pending_sub.end_date.date()
                        if pending_sub.end_date
                        else today + timedelta(days=30)
                    )
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
        context['url_list'] = reverse_lazy('commercial:factura_list')
        context['items_formset'] = InvoiceItemFormSet(prefix='items')
        commercial_services = Service.objects.filter(service_type=Service.COMMERCIAL)
        # The manual lines need `service_category` to tell months from days, and
        # the browser cannot derive the unit from the dates alone.
        context['commercial_services_json'] = json.dumps(
            list(commercial_services.values('id', 'code', 'title', 'price', 'service_category')),
            cls=DjangoJSONEncoder,
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
            groups = {}
            for sub in subscriptions:
                sub_start = sub.start_date.date() if sub.start_date else start_date
                sub_end = sub.end_date.date() if sub.end_date else end_date
                key = (sub_start, sub_end)
                groups.setdefault(key, []).append(sub)

            for (sub_start, sub_end), subs in groups.items():
                self.process_batch_invoice(customer, sub_start, sub_end, commercial_registry, subs)

            messages.success(
                self.request,
                f'Se generaron {len(groups)} factura(s) según los períodos de las suscripciones.',
            )
            return redirect(self.success_url)
        else:
            return self.process_manual_invoice(
                form, customer, start_date, end_date, commercial_registry
            )

    def anchor_invoice(self, invoice, subscriptions):
        """Cuelga la factura de la suscripción cuando hay una sola.

        `Invoice.subscription` es un atajo de conveniencia: con varias
        suscripciones no hay una respuesta única, así que se deja en NULL y el
        vínculo real queda en cada línea. Cuando hay exactamente una se
        completa, porque `subscription.invoices` es la relación que consulta
        buena parte del código.
        """
        unique = {sub.pk: sub for sub in subscriptions}
        if len(unique) == 1:
            invoice.subscription = next(iter(unique.values()))
            invoice.save(update_fields=['subscription'])
        return invoice

    def process_batch_invoice(
        self, customer, start_date, end_date, commercial_registry, subscriptions
    ):
        invoice = Invoice.objects.create(
            subscription=None, customer=customer, amount=0, number=self.generate_invoice_number()
        )
        total = 0
        items = []
        for sub in subscriptions:
            price = sub.service.price or 0
            quantity = sub.quantity
            amount = price * quantity
            unidad_medida = 'MES' if sub.service.service_category == 'agrometeo' else 'DÍA'
            item = InvoiceItem.objects.create(
                invoice=invoice,
                subscription=sub,
                codigo=sub.service.code or '',
                descripcion=sub.service.title,
                cantidad=quantity,
                unidad_medida=unidad_medida,
                precio=price,
                importe=amount,
            )
            items.append(item)
            total += amount

            sub.start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            sub.end_date = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
            sub.payment_status = 'pending'
            sub.save()

            contract, created = Contract.objects.get_or_create(
                subscription=sub,
                defaults={
                    'number': self.generate_contract_number(),
                    'date': timezone.now().date(),
                    'commercial_registry': commercial_registry,
                },
            )
            if not created:
                contract.commercial_registry = commercial_registry
                contract.save(update_fields=['commercial_registry'])

            log_action(
                user=self.request.user,
                obj=sub,
                action_flag=CHANGE,
                message=(
                    f'Suscripción facturada en lote: {sub.service.title} '
                    f'para {sub.customer.company_name}'
                ),
            )

        invoice.amount = total
        invoice.save()
        self.anchor_invoice(invoice, subscriptions)

        log_action(
            user=self.request.user,
            obj=invoice,
            action_flag=ADDITION,
            message=(
                f'Factura por lote {invoice.number} - Cliente: '
                f'{customer.company_name} - Monto: ${total:.2f}'
            ),
            request=self.request,
        )

        site_url = self.request.build_absolute_uri('/')
        generate_invoice_pdf_and_email_task(str(invoice.uuid), site_url)

    def process_manual_invoice(self, form, customer, start_date, end_date, commercial_registry):
        items_formset = InvoiceItemFormSet(self.request.POST, prefix='items')
        if not items_formset.is_valid():
            messages.error(self.request, 'Corrige los errores en las líneas de factura.')
            context = self.get_context_data(form=form)
            context['items_formset'] = items_formset
            return self.render_to_response(context)

        invoice = Invoice.objects.create(
            subscription=None, customer=customer, amount=0, number=self.generate_invoice_number()
        )
        total = 0
        items = []
        created_subs = []

        for item_form in items_formset:
            if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                cd = item_form.cleaned_data
                service = cd['service']
                cantidad = cd['cantidad']
                unidad_medida = 'MES' if service.service_category == 'agrometeo' else 'DÍA'

                sub = ServiceSubscription.objects.create(
                    customer=customer,
                    service=service,
                    start_date=timezone.make_aware(
                        datetime.combine(start_date, datetime.min.time())
                    ),
                    end_date=timezone.make_aware(datetime.combine(end_date, datetime.min.time())),
                    payment_status='pending',
                    record_active=True,
                    quantity=cantidad,
                )

                created_subs.append(sub)

                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    subscription=sub,
                    codigo=cd.get('codigo', service.code or ''),
                    descripcion=service.title,
                    cantidad=cantidad,
                    unidad_medida=cd.get('unidad_medida') or unidad_medida,
                    precio=cd['precio'],
                    importe=cantidad * cd['precio'],
                )
                items.append(item)
                total += cantidad * cd['precio']

                log_action(
                    user=self.request.user,
                    obj=sub,
                    action_flag=ADDITION,
                    message=(
                        f'Suscripción creada manualmente: {customer.company_name} - {service.title}'
                    ),
                )

        invoice.amount = total
        invoice.save()
        self.anchor_invoice(invoice, created_subs)

        log_action(
            user=self.request.user,
            obj=invoice,
            action_flag=ADDITION,
            message=(
                f'Factura manual {invoice.number} - Cliente: '
                f'{customer.company_name} - Monto: ${total:.2f}'
            ),
            request=self.request,
        )

        site_url = self.request.build_absolute_uri('/')
        generate_invoice_pdf_and_email_task(str(invoice.uuid), site_url)
        messages.success(self.request, 'Factura manual generada (con suscripciones creadas).')
        return redirect(self.success_url)

    def generate_invoice_number(self):
        year = timezone.now().year
        last = Invoice.objects.filter(issue_date__year=year).order_by('-issue_date').first()
        if last and last.number:
            try:
                num = int(last.number.split('-')[-1])
                return f'{year}-{num + 1:04d}'
            except ValueError, IndexError:
                pass
        return f'{year}-0001'

    def generate_contract_number(self):
        year = timezone.now().year
        last_contract = Contract.objects.filter(date__year=year).order_by('-date').first()
        if last_contract and last_contract.number:
            try:
                num = int(last_contract.number.split('-')[-1])
                return f'{year}-{num + 1:04d}'
            except ValueError, IndexError:
                pass
        return f'{year}-0001'


class InvoicePDFDownloadView(ServeModelFileView):
    model = Invoice
    field = 'pdf'
    permission_required = 'commercial.view_invoice'

    def get_queryset(self):
        return super().get_queryset().select_related('subscription')

    def get_permission_required(self, obj):
        """Staff con permiso, o el cliente titular de la factura.

        El cliente ve sus PDFs en "Mis Suscripciones" (dashboard) y en el
        portal; sin esto los botones Ver PDF/Descargar de sus propias facturas
        devuelven 403 porque no tienen ``commercial.view_invoice``.
        """
        user = self.request.user
        if not hasattr(user, 'commercial_customer'):
            return self.permission_required
        customer = user.commercial_customer
        if obj.customer_id == customer.pk:
            return None
        if obj.subscription_id and obj.subscription.customer_id == customer.pk:
            return None
        return self.permission_required

    def get_filename(self, obj):
        return f'factura_{obj.number}_{obj.issue_date:%Y-%m-%d}.pdf'

    def get(self, request, uuid):
        invoice = self.get_object()
        perm = self.get_permission_required(invoice)
        if perm and not request.user.has_perm(perm):
            raise PermissionDenied
        if not getattr(invoice, self.field):
            # El PDF se genera por una tarea Huey; si no existe (p. ej. el
            # worker no corre en dev) lo generamos bajo demanda para no
            # ocultar los botones de Descargar / Ver PDF en el listado.
            self._generate_pdf_if_missing(invoice)
        return super().get(request, uuid)

    def _generate_pdf_if_missing(self, invoice):
        from apps.commercial.views.invoice_utils import generate_invoice_pdf_standalone

        customer = invoice.customer
        items = list(invoice.items.all())
        start_date = invoice.subscription.start_date if invoice.subscription else invoice.issue_date
        end_date = invoice.subscription.end_date if invoice.subscription else invoice.issue_date
        try:
            generate_invoice_pdf_standalone(invoice, customer, start_date, end_date, items)
            invoice.refresh_from_db(fields=[self.field])
        except Exception as exc:  # pragma: no cover - depends on WeasyPrint/Pango
            logger.exception(
                'Fallo la generación bajo demanda del PDF de la factura %s: %s',
                invoice.uuid,
                exc,
            )


class CancelInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'commercial.delete_invoice'

    def post(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)

        if invoice.is_cancelled:
            messages.warning(request, f'La factura {invoice.number} ya estaba anulada.')
            return redirect('commercial:factura_list')

        invoice.is_cancelled = True
        invoice.save()

        items_with_subs = invoice.items.filter(subscription__isnull=False).select_related(
            'subscription'
        )
        for item in items_with_subs:
            sub = item.subscription
            if sub.payment_status in ['pending', 'requested']:
                sub.payment_status = 'requested'
                sub.save()
                log_action(
                    user=request.user,
                    obj=sub,
                    action_flag=CHANGE,
                    message=(
                        f"Estado revertido a 'solicitado' por anulación de factura {invoice.number}"
                    ),
                )

        log_action(
            user=request.user,
            obj=invoice,
            action_flag=CHANGE,
            message=f'Factura {invoice.number} anulada',
        )
        messages.success(request, f'Factura {invoice.number} anulada correctamente.')
        return redirect('commercial:factura_list')


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
            message=f'Factura {invoice.number} eliminada permanentemente',
        )
        invoice.hard_delete()
        messages.success(request, f'Factura {invoice_number} eliminada permanentemente.')
        return redirect('commercial:factura_list')


class ResendInvoiceEmailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'commercial.change_invoice'

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
            messages.error(
                request, 'No se pudo determinar el cliente o no tiene correo electrónico.'
            )
            return redirect('commercial:factura_list')

        exito = enviar_correo_factura(invoice, customer, request=request)
        if exito:
            messages.success(
                request, f'Correo de la factura {invoice.number} reenviado correctamente.'
            )
        else:
            messages.error(
                request,
                f'No se pudo reenviar el correo de la factura {invoice.number}. Revise los logs.',
            )
        return redirect('commercial:factura_list')


@login_required
@permission_required('commercial.view_subscription')
def ajax_pending_subscriptions(request):
    customer_id = request.GET.get('customer')
    if not customer_id:
        return HttpResponse('')
    qs = ServiceSubscription.objects.filter(
        customer_id=customer_id, payment_status__in=['requested', 'pending'], record_active=True
    ).select_related('service')
    if not request.user.is_staff and not request.user.is_superuser:
        qs = qs.filter(customer__user=request.user)
    subs = qs
    if not subs.exists():
        return HttpResponse('<p class="text-muted">No hay suscripciones pendientes.</p>')
    html = ''
    for sub in subs:
        start_str = sub.start_date.strftime('%Y-%m-%d') if sub.start_date else ''
        end_str = sub.end_date.strftime('%Y-%m-%d') if sub.end_date else ''
        days = (sub.end_date - sub.start_date).days if sub.start_date and sub.end_date else 0
        title = escape(sub.service.title or '')
        summary = escape(sub.service.summary or '')
        html += f'''
        <div class="form-check">
          <input class="form-check-input subscription-check" type="checkbox"
                 name="subscriptions" value="{sub.pk}"
                 id="sub_{sub.pk}" data-start="{start_str}" data-end="{end_str}"
                 data-quantity="{sub.quantity}"
                 data-service="{title}" data-days="{days}" data-summary="{summary}">
          <label class="form-check-label" for="sub_{sub.pk}">
            <strong>{title}</strong>
            <br><small class="text-muted">{summary}</small>
          </label>
        </div>
        '''
    return HttpResponse(html)
