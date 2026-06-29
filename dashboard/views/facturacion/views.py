
import json
import os
from datetime import datetime, timedelta

import pdfkit
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, reverse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, ListView

from common.utils import log_action
from dashboard.forms.company.forms import CompanySettingsForm
from dashboard.forms.facturacion.forms import InvoiceForm, InvoiceItemFormSet
from dashboard.models import (
    CompanySettings,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)


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
            return self.process_batch_invoice(form, customer, start_date, end_date, commercial_registry, subscriptions)
        else:
            return self.process_manual_invoice(form, customer, start_date, end_date, commercial_registry)

    def process_batch_invoice(self, form, customer, start_date, end_date, commercial_registry, subscriptions):
        days_count = (end_date - start_date).days
        invoice = Invoice.objects.create(
            subscription=None,
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
            sub.start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            sub.end_date = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
            sub.payment_status = 'pending'
            sub.save()

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

        self.generate_pdf(invoice, customer, start_date, end_date, commercial_registry, items)
        self.send_invoice_email(invoice, customer)  # Envío de correo
        messages.success(self.request, "Factura por lote generada.")
        return redirect(self.success_url)

    def process_manual_invoice(self, form, customer, start_date, end_date, commercial_registry):
        items_formset = InvoiceItemFormSet(self.request.POST, prefix='items')
        if not items_formset.is_valid():
            messages.error(self.request, "Corrige los errores en las líneas de factura.")
            context = self.get_context_data(form=form)
            context['items_formset'] = items_formset
            return self.render_to_response(context)

        invoice = Invoice.objects.create(
            subscription=None,
            amount=0,
            number=self.generate_invoice_number()
        )
        total = 0
        items = []
        for item_form in items_formset:
            if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                cd = item_form.cleaned_data
                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    codigo=cd.get('codigo', ''),
                    descripcion=cd['service'].title,
                    cantidad=cd['cantidad'],
                    unidad_medida=cd.get('unidad_medida', 'U'),
                    precio=cd['precio'],
                    importe=cd['cantidad'] * cd['precio'],
                )
                items.append(item)
                total += cd['cantidad'] * cd['precio']
        invoice.amount = total
        invoice.save()

        log_action(
            user=self.request.user,
            obj=invoice,
            action_flag=ADDITION,
            message=f"Factura manual {invoice.number} - Cliente: {customer.company_name} - Monto: ${total:.2f}"
        )

        self.generate_pdf(invoice, customer, start_date, end_date, commercial_registry, items)
        self.send_invoice_email(invoice, customer)  # Envío de correo
        messages.success(self.request, "Factura manual generada.")
        return redirect(self.success_url)

    def send_invoice_email(self, invoice, customer):
        """
        Envía la factura en PDF al correo del cliente.
        Reutiliza factura_qr.html si hay suscripción con pago QR;
        en caso contrario, factura.html (que ahora soporta subscription=None).
        """
        if not customer.user or not customer.user.email:
            return

        # Obtener la primera suscripción asociada a algún item de la factura (si existe)
        first_item = invoice.items.first()
        subscription = first_item.subscription if first_item else None

        # Seleccionar plantilla según método de pago
        if subscription and subscription.payment_method == 'qr':
            template = 'pages/dashboard/emails/factura_qr.html'
        else:
            template = 'pages/dashboard/emails/factura.html'

        company = CompanySettings.get_instance()
        base_url = self.request.build_absolute_uri('/')
        context = {
            'invoice': invoice,
            'customer': customer,
            'subscription': subscription,          # Puede ser None
            'payment_method': subscription.get_payment_method_display() if subscription else '',
            'company': company,
            'index_url': base_url,
            'listado_url': self.request.build_absolute_uri(reverse('listado_facturas')),
            'current_year': timezone.now().year,
        }

        html_content = render_to_string(template, context)
        subject = f"Factura {invoice.number} - {customer.company_name}"

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer.user.email],
        )
        email.content_subtype = "html"

        # Adjuntar PDF
        if invoice.pdf and invoice.pdf.storage.exists(invoice.pdf.name):
            with invoice.pdf.storage.open(invoice.pdf.name, 'rb') as f:
                email.attach(f'factura_{invoice.number}.pdf', f.read(), 'application/pdf')

        # Adjuntar QR si corresponde
        if subscription and subscription.payment_method == 'qr':
            from django.contrib.staticfiles import finders
            qr_path = finders.find('dist/img/QR/QR.png')
            if not qr_path:
                qr_path = os.path.join(settings.STATIC_ROOT, 'dist/img/QR/QR.png')
            if os.path.exists(qr_path):
                with open(qr_path, 'rb') as f:
                    email.attach('qr_pago.png', f.read(), 'image/png')

        email.send()

    def generate_pdf(self, invoice, customer, start_date, end_date, commercial_registry, items):
        company = CompanySettings.get_instance()
        periodo = f"Desde {start_date.strftime('%d/%m/%Y')} hasta {end_date.strftime('%d/%m/%Y')}"
        context = {
            'numero_factura': invoice.number,
            'fecha_facturacion': invoice.issue_date.strftime('%d de %B del %Y'),
            'periodo_facturacion': periodo,
            'cliente': {
                'nombre': customer.company_name,
                'direccion': customer.address,
                'codigo_reeup': customer.reeup or '',
                'nit': customer.nit or '',
                'cuenta_bancaria': customer.account or '',
                'agencia_bancaria': customer.agency_bank or '',
                'telefonos': customer.phone or '',
            },
            'proveedor': {
                'nombre': company.nombre,
                'direccion': company.direccion,
                'codigo_reeup': company.codigo_reeup,
                'nit': company.nit,
                'cuenta_bancaria': company.cuenta_bancaria,
                'agencia_bancaria': company.agencia_bancaria,
                'telefonos': company.telefonos,
                'registro_comercial': commercial_registry,
                'no_contrato': '',
                'fecha_contrato': '',
            },
            'items': [{
                'codigo': item.codigo,
                'descripcion': item.descripcion,
                'cantidad': item.cantidad,
                'unidad_medida': item.unidad_medida,
                'precio': item.precio,
                'importe': item.importe,
            } for item in items],
            'total': float(invoice.amount),
            'current_year': timezone.now().year,
        }
        html_string = render_to_string('pages/dashboard/suscripciones/factura_template.html', context)
        options = {
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'margin-right': '10mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None,
        }
        pdf_bytes = pdfkit.from_string(html_string, False, options=options)
        filename = f"factura_{invoice.id}.pdf"
        invoice.pdf.save(filename, ContentFile(pdf_bytes))

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


def ajax_pending_subscriptions(request):
    customer_id = request.GET.get('customer')
    if not customer_id:
        return HttpResponse('')
    subs = ServiceSubscription.objects.filter(
        customer_id=customer_id,
        payment_status__in=['requested', 'pending'],
        record_active=True
    )
    if not subs.exists():
        return HttpResponse('<p class="text-muted">No hay suscripciones pendientes para este cliente.</p>')
    html = ''
    for sub in subs:
        html += f'<div class="form-check"><input class="form-check-input" type="checkbox" name="subscriptions" value="{sub.pk}" id="sub_{sub.pk}"><label class="form-check-label" for="sub_{sub.pk}">{sub.service.title} ({sub.status_display})</label></div>'
    return HttpResponse(html)


class CompanySettingsAjaxUpdateView(View):
    def post(self, request, *args, **kwargs):
        instance = CompanySettings.get_instance()
        form = CompanySettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

