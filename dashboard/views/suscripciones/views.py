from datetime import timedelta
from io import BytesIO

from dashboard.forms.suscripciones.forms import (
    CertificateUploadForm,
    InvoiceAmountForm,
    SubscriptionForm,
)
from dashboard.models import Certificate, Customer, Invoice, ServiceSubscription
from django.conf import settings
from django.contrib import messages
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
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


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
            return qs.order_by('-start_date')
        elif user.groups.filter(name='Clientes').exists():
            try:
                customer = user.customer
                return qs.filter(customer=customer).order_by('-start_date')
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Suscripción'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['url_list'] = reverse_lazy('listado_suscripciones')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Suscripción creada con éxito.')
        return super().form_valid(form)


class SubscriptionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ServiceSubscription
    form_class = SubscriptionForm
    template_name = 'pages/dashboard/suscripciones/actualizar_suscripcion.html'
    permission_required = 'dashboard.change_subscription'
    success_url = reverse_lazy('listado_suscripciones')

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
        messages.success(self.request, 'Suscripción actualizada con éxito.')
        return super().form_valid(form)


class SubscriptionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ServiceSubscription
    template_name = 'pages/dashboard/suscripciones/eliminar_suscripcion.html'
    permission_required = 'dashboard.delete_subscription'
    success_url = reverse_lazy('listado_suscripciones')

    def get_object(self, queryset=None):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Suscripción eliminada con éxito.')
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Suscripción'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['url_list'] = reverse_lazy('listado_suscripciones')
        return context


class SubscriptionRenewView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ServiceSubscription
    fields = []
    template_name = 'pages/dashboard/suscripciones/renovar_suscripcion.html'
    success_url = reverse_lazy('listado_suscripciones')

    def get_object(self, queryset=None):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def test_func(self):
        sub = self.get_object()
        return (self.request.user.groups.filter(name='Clientes').exists() and
                hasattr(self.request.user, 'customer') and
                sub.customer == self.request.user.customer)

    def form_valid(self, form):
        old = self.object
        ServiceSubscription.objects.create(
            customer=old.customer,
            service=old.service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            payment_status='requested'
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


class GenerateInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'pages/dashboard/suscripciones/generar_factura.html'
    form_class = InvoiceAmountForm
    permission_required = 'dashboard.change_subscription'
    success_url = reverse_lazy('listado_suscripciones')

    def dispatch(self, request, *args, **kwargs):
        self.subscription = get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])
        if self.subscription.payment_status != 'requested':
            messages.error(request, "Esta suscripción no está en estado solicitado.")
            return redirect('listado_suscripciones')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscription'] = self.subscription
        context['title'] = 'Generar Factura'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        return context

    def form_valid(self, form):
        amount = form.cleaned_data['amount']

        # Crear factura (número único)
        invoice = Invoice(
            subscription=self.subscription,
            amount=amount,
            number=f"INV-{self.subscription.uuid}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )

        # --- Generar PDF de la factura (igual que antes) ---
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        p.setFont("Helvetica-Bold", 16)
        p.drawString(2*cm, height-3*cm, "FACTURA")
        p.setFont("Helvetica", 12)
        p.drawString(2*cm, height-5*cm, f"Nº: {invoice.number}")
        p.drawString(2*cm, height-6*cm, f"Fecha: {timezone.now().strftime('%d/%m/%Y')}")
        p.drawString(2*cm, height-7*cm, f"Cliente: {self.subscription.customer.company_name}")
        p.drawString(2*cm, height-8*cm, f"NIT: {self.subscription.customer.nit}")
        p.drawString(2*cm, height-9*cm, f"Servicio: {self.subscription.service.title}")
        p.drawString(2*cm, height-10*cm, f"Período: {self.subscription.start_date.strftime('%d/%m/%Y')} - {self.subscription.end_date.strftime('%d/%m/%Y')}")
        p.drawString(2*cm, height-11*cm, f"Importe: {amount} CUP")
        p.showPage()
        p.save()
        # ------------------------------------------------

        filename = f"factura_{self.subscription.uuid}.pdf"
        invoice.pdf.save(filename, ContentFile(buffer.getvalue()))
        invoice.save()

        # Actualizar estado
        self.subscription.payment_status = 'pending'
        self.subscription.save()

        # Enviar correo (con QR si corresponde)
        self.send_payment_email(self.subscription, invoice)

        messages.success(self.request, "Factura generada y enviada al cliente.")
        return redirect(self.success_url)

    def send_payment_email(self, subscription, invoice):
        """Envía correo con factura adjunta y, si el método es QR, incluye la imagen QR estática."""
        # Determinar asunto y plantilla según método de pago
        if subscription.payment_method == 'qr':
            subject = f"Factura y pago QR - {subscription.service.title}"
            template = 'pages/dashboard/emails/factura_qr.html'
        else:
            subject = f"Factura - {subscription.service.title}"
            template = 'pages/dashboard/emails/factura.html'

        # Renderizar HTML
        context = {
            'subscription': subscription,
            'invoice': invoice,
            'customer': subscription.customer,
            'payment_method': subscription.get_payment_method_display(),  # texto legible
        }
        html_content = render_to_string(template, context)

        # Crear correo
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscription.customer.user.email]
        )
        email.content_subtype = "html"

        # Adjuntar factura PDF
        if invoice.pdf:
            email.attach_file(invoice.pdf.path)

        # Si el método de pago es QR, adjuntar la imagen estática
        if subscription.payment_method == 'qr':
            # Localizar la imagen QR en los archivos estáticos
            from django.contrib.staticfiles import finders
            import os

            qr_path = finders.find('dist/img/QR/QR.png')
            if not qr_path:
                # Fallback: construir ruta con STATIC_ROOT
                qr_path = os.path.join(settings.STATIC_ROOT, 'dist/img/QR/QR.png')

            if os.path.exists(qr_path):
                with open(qr_path, 'rb') as f:
                    email.attach('qr_pago.png', f.read(), 'image/png')
            else:
                # Opcional: loguear error, pero no impedir envío
                print("No se encontró la imagen QR en", qr_path)

        # Enviar
        email.send()


class ApproveSubscriptionView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ServiceSubscription
    form_class = CertificateUploadForm
    template_name = 'pages/dashboard/suscripciones/subir_certificado.html'
    permission_required = 'dashboard.change_subscription'
    success_url = reverse_lazy('listado_suscripciones')

    def get_object(self, queryset=None):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # No pasamos instance al formulario porque el modelo del form es Certificate, no Subscription
        kwargs.pop('instance', None)
        return kwargs

    def form_valid(self, form):
        sub = self.get_object()
        if sub.payment_status != 'pending':
            messages.error(self.request, "Esta suscripción no está pendiente de pago.")
            return redirect(self.success_url)

        # Crear certificado asociado a la suscripción
        certificate = Certificate(
            subscription=sub,
            pdf=form.cleaned_data['pdf']
        )
        certificate.save()

        # Actualizar estado de suscripción
        sub.payment_status = 'paid'
        sub.save()

        # Enviar correo al cliente con el certificado
        self.send_certificate_email(sub, certificate)

        messages.success(self.request, "Pago aprobado y certificado enviado.")
        return redirect(self.success_url)

    def send_certificate_email(self, subscription, certificate):

        subject = f"Certificado de {subscription.service.title}"
        message = render_to_string('pages/dashboard/emails/certificado.html', {'subscription': subscription})
        email = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [subscription.customer.user.email]
        )
        if certificate.pdf:
            email.attach_file(certificate.pdf.path)
        email.send()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aprobar pago y subir certificado'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['subscription'] = self.get_object()
        return context
