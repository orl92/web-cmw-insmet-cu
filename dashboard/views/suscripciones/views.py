from datetime import timedelta
from io import BytesIO

from dashboard.forms.suscripciones.forms import CertificateUploadForm, SubscriptionForm
from dashboard.models import Customer, ServiceSubscription
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
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View
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


class GenerateInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.change_subscription'

    def get_object(self):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def post(self, request, *args, **kwargs):
        sub = self.get_object()
        if sub.payment_status != 'requested':
            messages.error(request, "Esta suscripción no está en estado solicitado.")
            return redirect('listado_suscripciones')

        # Generar PDF de factura
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        p.setFont("Helvetica-Bold", 16)
        p.drawString(2*cm, height-3*cm, "FACTURA")
        p.setFont("Helvetica", 12)
        p.drawString(2*cm, height-5*cm, f"Nº: {sub.uuid}")
        p.drawString(2*cm, height-6*cm, f"Fecha: {timezone.now().strftime('%d/%m/%Y')}")
        p.drawString(2*cm, height-7*cm, f"Cliente: {sub.customer.company_name}")
        p.drawString(2*cm, height-8*cm, f"NIT: {sub.customer.nit}")
        p.drawString(2*cm, height-9*cm, f"Servicio: {sub.service.title}")
        p.drawString(2*cm, height-10*cm, f"Período: {sub.start_date.strftime('%d/%m/%Y')} - {sub.end_date.strftime('%d/%m/%Y')}")
        p.drawString(2*cm, height-11*cm, "Importe: 100.00 CUP")  # Ajustar según lógica

        p.showPage()
        p.save()

        filename = f"factura_{sub.uuid}.pdf"
        sub.invoice.save(filename, ContentFile(buffer.getvalue()))
        sub.payment_status = 'pending'
        sub.save()

        # Opcional: enviar correo
        # asunto = f"Factura de servicio: {sub.service.title}"
        # mensaje = render_to_string('emails/factura_generada.html', {'subscription': sub})
        # email = EmailMessage(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [sub.customer.user.email])
        # email.attach_file(sub.invoice.path)
        # email.send()

        messages.success(request, "Factura generada correctamente.")
        return redirect('listado_suscripciones')


class ApproveSubscriptionView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ServiceSubscription
    form_class = CertificateUploadForm
    template_name = 'pages/dashboard/suscripciones/subir_certificado.html'
    permission_required = 'dashboard.change_subscription'
    success_url = reverse_lazy('listado_suscripciones')

    def get_object(self, queryset=None):
        return get_object_or_404(ServiceSubscription, uuid=self.kwargs['uuid'])

    def form_valid(self, form):
        sub = self.object
        if sub.payment_status != 'pending':
            messages.error(self.request, "Esta suscripción no está pendiente de pago.")
            return redirect(self.success_url)
        sub = form.save(commit=False)
        sub.payment_status = 'paid'
        sub.save()
        messages.success(self.request, "Pago aprobado y certificado subido.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Subir certificado y aprobar pago'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['url_list'] = reverse_lazy('listado_suscripciones')
        return context
