import pdfkit 
import base64
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
    View,
)

from common.utils import log_action
from dashboard.forms.suscripciones.forms import (
    CertificateUploadForm,
    InvoiceForm,
    SubscriptionForm,
)
from dashboard.models import Certificate, Contract, Customer, Invoice, ServiceSubscription


class SubscriptionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ServiceSubscription
    template_name = 'pages/dashboard/suscripciones/listado_suscripciones.html'
    context_object_name = 'objects'
    paginate_by = 20
    permission_required = 'dashboard.view_subscription'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset().select_related('customer', 'service')
        if user.is_superuser or user.is_staff:
            # Staff ve todas, incluyendo desactivadas (record_active=False)
            return qs.order_by('-start_date')
        elif user.groups.filter(name='Clientes').exists():
            try:
                customer = user.customer
                # Clientes solo ven registros activos (record_active=True)
                return qs.filter(customer=customer, record_active=True).order_by('-start_date')
            except Customer.DoesNotExist:
                return qs.none()
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mis Suscripciones' if not self.request.user.is_staff else 'Todas las Suscripciones'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
        context['now'] = timezone.now()
        if context['is_staff']:
            context['btn'] = 'Añadir Suscripción'
            context['url_create'] = reverse_lazy('crear_suscripcion')
        return context


class SubscriptionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ServiceSubscription
    form_class = SubscriptionForm
    template_name = 'pages/dashboard/suscripciones/crear_suscripcion.html'
    permission_required = 'dashboard.add_subscription'
    success_url = reverse_lazy('listado_suscripciones')
    url_redirect = success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Suscripción'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['url_list'] = reverse_lazy('listado_suscripciones')
        return context

    def form_valid(self, form):
        # Aseguramos que la nueva suscripción tenga record_active=True
        form.instance.record_active = True
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Suscripción creada para: {self.object.customer.company_name} - {self.object.service.title}"
        )
        messages.success(self.request, 'Suscripción creada con éxito.')
        return response


class SubscriptionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ServiceSubscription
    form_class = SubscriptionForm
    template_name = 'pages/dashboard/suscripciones/actualizar_suscripcion.html'
    permission_required = 'dashboard.change_subscription'
    success_url = reverse_lazy('listado_suscripciones')
    url_redirect = success_url

    def get_object(self, queryset=None):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Suscripción'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['url_list'] = reverse_lazy('listado_suscripciones')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Suscripción actualizada para: {self.object.customer.company_name} - {self.object.service.title}"
        )
        messages.success(self.request, 'Suscripción actualizada con éxito.')
        return response


class GenerateInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'pages/dashboard/suscripciones/generar_factura.html'
    form_class = InvoiceForm
    permission_required = 'dashboard.change_subscription'
    success_url = reverse_lazy('listado_suscripciones')

    def dispatch(self, request, *args, **kwargs):
        self.subscription = get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])
        if self.subscription.payment_status != 'requested':
            messages.error(request, "Esta suscripción no está en estado solicitado.")
            return redirect('listado_suscripciones')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        today = timezone.now().date()
        initial['start_date'] = today.isoformat()
        initial['end_date'] = (today + timedelta(days=30)).isoformat()
        initial['amount'] = 0
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscription'] = self.subscription
        context['title'] = 'Generar Factura'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['url_list'] = reverse_lazy('listado_suscripciones')
        return context

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        commercial_registry = form.cleaned_data['commercial_registry']  # Campo obligatorio

        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))

        self.subscription.start_date = start_datetime
        self.subscription.end_date = end_datetime
        self.subscription.payment_status = 'pending'
        self.subscription.save()

        # Crear o actualizar contrato con el registro comercial ingresado
        contract, created = Contract.objects.get_or_create(
            subscription=self.subscription,
            defaults={
                'number': self.generate_contract_number(),
                'date': timezone.now().date(),
                'commercial_registry': commercial_registry,
            }
        )

        # Si el contrato ya existía, actualizar su registro comercial (útil para regeneración)
        if not created:
            contract.commercial_registry = commercial_registry
            contract.save(update_fields=['commercial_registry'])

        # Número de factura secuencial
        invoice_number = self.generate_invoice_number()
        invoice = Invoice(
            subscription=self.subscription,
            amount=amount,
            number=invoice_number,
        )
        invoice.save()  # Guardamos para que se asigne issue_date

        # Generar PDF
        context = self.get_invoice_context(invoice, start_date, end_date, contract)
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

        filename = f"factura_{self.subscription.uuid}.pdf"
        invoice.pdf.save(filename, ContentFile(pdf_bytes))

        # Logs
        log_action(
            user=self.request.user,
            obj=self.subscription,
            action_flag=CHANGE,
            message=f"Factura {invoice.number} generada, estado cambiado a pendiente"
        )
        log_action(
            user=self.request.user,
            obj=invoice,
            action_flag=ADDITION,
            message=f"Factura creada por {amount} CUP"
        )

        # Enviar correo
        self.send_payment_email(self.request, self.subscription, invoice)

        messages.success(self.request, "Factura generada, período asignado y correo enviado.")
        return redirect(self.success_url)

    def generate_invoice_number(self):
        year = timezone.now().year
        last_invoice = Invoice.objects.filter(issue_date__year=year).order_by('-issue_date').first()
        if last_invoice and last_invoice.number:
            try:
                last_num = int(last_invoice.number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        return f"{year}-{new_num:04d}"

    def generate_contract_number(self):
        year = timezone.now().year
        last_contract = Contract.objects.filter(date__year=year).order_by('-date').first()
        if last_contract and last_contract.number:
            try:
                last_num = int(last_contract.number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        return f"{year}-{new_num:04d}"

    def get_invoice_context(self, invoice, start_date, end_date, contract):
        subscription = self.subscription
        customer = subscription.customer
        service = subscription.service
        proveedor = settings.PROVEEDOR_FACTURA

        periodo = f"Desde {start_date.strftime('%d/%m/%Y')} hasta {end_date.strftime('%d/%m/%Y')}"

        items = [{
            'codigo': service.uuid.hex[:15].upper(),
            'descripcion': service.title,
            'cantidad': 1,
            'unidad_medida': 'U',
            'precio': float(invoice.amount),
            'importe': float(invoice.amount),
        }]

        # Logo a base64
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'dist', 'img', 'logo.png')
        logo_base64 = ''
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')

        fecha_facturacion = invoice.issue_date.strftime('%d de %B del %Y') if invoice.issue_date else timezone.now().strftime('%d de %B del %Y')
        contract_date_str = contract.date.strftime('%d/%m/%Y') if contract.date else ''

        context = {
            'numero_factura': invoice.number,
            'fecha_facturacion': fecha_facturacion,
            'periodo_facturacion': periodo,
            'cliente': {
                'nombre': customer.company_name,
                'direccion': customer.address,
                'codigo_reeup': customer.reeup or '',
                'nit': customer.nit or '',
                'cuenta_bancaria': customer.account or '',
                'agencia_bancaria': getattr(customer, 'agency_bank', '') or '',
                'telefonos': customer.phone or '',
            },
            'proveedor': {
                'nombre': proveedor['nombre'],
                'direccion': proveedor['direccion'],
                'codigo_reeup': proveedor['codigo_reeup'],
                'nit': proveedor['nit'],
                'cuenta_bancaria': proveedor['cuenta_bancaria'],
                'agencia_bancaria': proveedor['agencia_bancaria'],
                'telefonos': proveedor['telefonos'],
                'registro_comercial': contract.commercial_registry,
                'no_contrato': contract.number,
                'fecha_contrato': contract_date_str,
            },
            'items': items,
            'total': float(invoice.amount),
            'logo_base64': logo_base64,
            'current_year': timezone.now().year,
        }
        return context

    def send_payment_email(self, request, subscription, invoice):
        if subscription.payment_method == 'qr':
            subject = f"Factura y pago QR - {subscription.service.title}"
            template = 'pages/dashboard/emails/factura_qr.html'
        else:
            subject = f"Factura - {subscription.service.title}"
            template = 'pages/dashboard/emails/factura.html'

        base_url = request.build_absolute_uri('/')
        context = {
            'subscription': subscription,
            'invoice': invoice,
            'customer': subscription.customer,
            'payment_method': subscription.get_payment_method_display(),
            'index_url': base_url,
            'listado_url': request.build_absolute_uri(reverse('listado_suscripciones')),
            'current_year': timezone.now().year,
        }
        html_content = render_to_string(template, context)

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscription.customer.user.email]
        )
        email.content_subtype = "html"

        if invoice.pdf and invoice.pdf.storage.exists(invoice.pdf.name):
            with invoice.pdf.storage.open(invoice.pdf.name, 'rb') as f:
                email.attach(f'factura_{invoice.number}.pdf', f.read(), 'application/pdf')

        if subscription.payment_method == 'qr':
            from django.contrib.staticfiles import finders
            qr_path = finders.find('dist/img/QR/QR.png')
            if not qr_path:
                qr_path = os.path.join(settings.STATIC_ROOT, 'dist/img/QR/QR.png')
            if os.path.exists(qr_path):
                with open(qr_path, 'rb') as f:
                    email.attach('qr_pago.png', f.read(), 'image/png')

        email.send()

    def form_invalid(self, form):
        messages.error(self.request, "Corrige los errores del formulario.")
        return super().form_invalid(form)


class RegenerateInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.change_subscription'

    def post(self, request, *args, **kwargs):
        subscription = get_object_or_404(ServiceSubscription, uuid=kwargs['uuid'])

        if subscription.payment_status == 'paid':
            messages.error(request, "No se puede regenerar una factura de una suscripción ya pagada.")
            return redirect('listado_suscripciones')

        if not subscription.invoices.exists():
            messages.error(request, "Esta suscripción no tiene facturas para regenerar.")
            return redirect('listado_suscripciones')

        for invoice in subscription.invoices.all():
            invoice.is_cancelled = True
            invoice.save()
            log_action(
                user=request.user,
                obj=invoice,
                action_flag=CHANGE,
                message=f"Factura {invoice.number} anulada por regeneración"
            )

        subscription.certificates.all().delete()
        subscription.payment_status = 'requested'
        subscription.save()

        log_action(
            user=request.user,
            obj=subscription,
            action_flag=CHANGE,
            message="Facturas anuladas, estado revertido a solicitado para regenerar"
        )

        messages.success(request, "Factura anterior anulada. Ahora puede generar una nueva.")
        return redirect('facturar_suscripcion', uuid=subscription.uuid)


class SubscriptionRenewView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ServiceSubscription
    fields = []
    template_name = 'pages/dashboard/suscripciones/renovar_suscripcion.html'
    success_url = reverse_lazy('listado_suscripciones')
    url_redirect = success_url

    def get_object(self, queryset=None):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def test_func(self):
        sub = self.get_object()
        return (self.request.user.groups.filter(name='Clientes').exists() and
                hasattr(self.request.user, 'customer') and
                sub.customer == self.request.user.customer and
                sub.is_active)  # Propiedad de vigencia (pagada y no expirada)

    def form_valid(self, form):
        old = self.object
        new_sub = ServiceSubscription.objects.create(
            customer=old.customer,
            service=old.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            payment_status='requested',
            record_active=True
        )
        log_action(
            user=self.request.user,
            obj=new_sub,
            action_flag=ADDITION,
            message=f"Suscripción renovada desde {old.uuid}"
        )
        messages.success(self.request, 'Solicitud de renovación enviada. El staff generará una factura.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Renovar Suscripción'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['url_list'] = reverse_lazy('listado_suscripciones')
        context['subscription'] = self.get_object()
        return context


class SubscriptionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ServiceSubscription
    template_name = 'pages/dashboard/suscripciones/eliminar_suscripcion.html'
    permission_required = 'dashboard.delete_subscription'
    success_url = reverse_lazy('listado_suscripciones')
    url_redirect = success_url

    def get_object(self, queryset=None):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if request.user.is_superuser and request.POST.get('hard_delete') == 'true':
            self.object.hard_delete()
            log_action(
                user=request.user,
                obj=self.object,
                action_flag=DELETION,
                message=f"Suscripción eliminada físicamente: {self.object.customer.company_name} - {self.object.service.title}"
            )
            messages.success(request, 'Suscripción eliminada permanentemente.')
        else:
            self.object.delete()  # Soft delete (marca record_active=False)
            log_action(
                user=request.user,
                obj=self.object,
                action_flag=DELETION,
                message=f"Suscripción desactivada: {self.object.customer.company_name} - {self.object.service.title}"
            )
            messages.success(request, 'Suscripción desactivada con éxito.')

        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Desactivar Suscripción'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['url_list'] = reverse_lazy('listado_suscripciones')
        context['is_superuser'] = self.request.user.is_superuser
        return context


class ApproveSubscriptionView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ServiceSubscription
    form_class = CertificateUploadForm
    template_name = 'pages/dashboard/suscripciones/subir_certificado.html'
    permission_required = 'dashboard.change_subscription'
    success_url = reverse_lazy('listado_suscripciones')
    url_redirect = success_url

    def get_object(self, queryset=None):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        return kwargs

    def form_valid(self, form):
        sub = self.get_object()
        if sub.payment_status != 'pending':
            messages.error(self.request, "Esta suscripción no está pendiente de pago.")
            return redirect(self.success_url)

        certificate = Certificate(
            subscription=sub,
            pdf=form.cleaned_data['pdf']
        )
        certificate.save()

        sub.payment_status = 'paid'
        sub.save()

        self.send_certificate_email(self.request, sub, certificate)

        log_action(
            user=self.request.user,
            obj=sub,
            action_flag=CHANGE,
            message=f"Pago aprobado, certificado {certificate.pk} subido"
        )
        log_action(
            user=self.request.user,
            obj=certificate,
            action_flag=ADDITION,
            message=f"Certificado generado para suscripción {sub.uuid}"
        )

        messages.success(self.request, "Pago aprobado y certificado enviado.")
        return redirect(self.success_url)

    def send_certificate_email(self, request, subscription, certificate):
        subject = f"Certificado de {subscription.service.title}"
        base_url = request.build_absolute_uri('/')
        context = {
            'subscription': subscription,
            'index_url': base_url,
            'listado_url': request.build_absolute_uri(reverse('listado_suscripciones')),
            'current_year': timezone.now().year,
        }
        html_content = render_to_string('pages/dashboard/emails/certificado.html', context)

        email = EmailMessage(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            [subscription.customer.user.email]
        )
        email.content_subtype = "html"

        if certificate.pdf:
            email.attach_file(certificate.pdf.path)

        email.send()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aprobar pago y subir certificado'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['subscription'] = self.get_object()
        context['url_list'] = reverse_lazy('listado_suscripciones')
        return context
