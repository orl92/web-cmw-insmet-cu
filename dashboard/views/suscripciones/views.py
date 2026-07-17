import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    View,
)

from common.utils import log_action
from dashboard.forms.suscripciones.forms import (
    CertificateUploadForm,
    SubscriptionForm,
)
from dashboard.models import Certificate, Customer, ServiceSubscription

logger = logging.getLogger(__name__)


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
        context['url_export'] = reverse_lazy('exportar_csv_suscripciones')
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
                sub.is_active)

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
        """Envía el certificado por correo sin bloquear el proceso si falla."""
        enviar_correo_certificado(subscription, request=request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aprobar pago y subir certificado'
        context['parent'] = 'servicios'
        context['segment'] = 'suscripciones'
        context['subscription'] = self.get_object()
        context['url_list'] = reverse_lazy('listado_suscripciones')
        return context


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
        return redirect(f"{reverse('crear_factura')}?customer_uuid={subscription.customer.uuid}")


class SubscriptionCancelView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Anula (soft delete) una suscripción."""
    permission_required = 'dashboard.delete_subscription'

    def post(self, request, uuid):
        subscription = get_object_or_404(ServiceSubscription, uuid=uuid)

        if not subscription.record_active:
            messages.warning(request, "La suscripción ya estaba desactivada.")
            return redirect('listado_suscripciones')

        subscription.delete()  # soft delete (record_active=False)

        log_action(
            user=request.user,
            obj=subscription,
            action_flag=DELETION,
            message=f"Suscripción desactivada: {subscription.customer.company_name} - {subscription.service.title}"
        )
        messages.success(request, 'Suscripción desactivada con éxito.')
        return redirect('listado_suscripciones')


class SubscriptionHardDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Eliminación física permanente (solo superusuarios)."""
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, uuid):
        subscription = get_object_or_404(ServiceSubscription, uuid=uuid)
        customer_name = subscription.customer.company_name
        service_title = subscription.service.title

        subscription.hard_delete()

        log_action(
            user=request.user,
            obj=subscription,
            action_flag=DELETION,
            message=f"Suscripción eliminada físicamente: {customer_name} - {service_title}"
        )
        messages.success(request, f"Suscripción de {customer_name} eliminada permanentemente.")
        return redirect('listado_suscripciones')


def enviar_correo_certificado(subscription, request=None):
    """
    Envía el certificado de una suscripción por correo.
    Retorna True si se envió correctamente, False si falló o no hay certificado/correo.
    """
    if not subscription.customer.user or not subscription.customer.user.email:
        return False

    certificate = subscription.certificates.first()
    if not certificate:
        return False

    subject = f"Certificado de {subscription.service.title}"
    base_url = request.build_absolute_uri('/') if request else settings.BASE_URL
    context = {
        'subscription': subscription,
        'index_url': base_url,
        'listado_url': base_url + reverse('listado_suscripciones').lstrip('/'),
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

    try:
        email.send()
        return True
    except Exception as e:
        logger.error(f"Error enviando certificado: {e}")
        return False


class ResendCertificateEmailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.change_subscription'

    def get(self, request, uuid):
        subscription = get_object_or_404(ServiceSubscription, uuid=uuid)

        if subscription.payment_status != 'paid':
            messages.error(request, "Solo se pueden reenviar certificados de suscripciones pagadas.")
            return redirect('listado_suscripciones')

        if not subscription.certificates.exists():
            messages.error(request, "Esta suscripción no tiene certificado.")
            return redirect('listado_suscripciones')

        exito = enviar_correo_certificado(subscription, request=request)
        if exito:
            messages.success(request, f"Certificado de {subscription.service.title} reenviado correctamente.")
        else:
            messages.error(request, "No se pudo reenviar el certificado. Revise los logs.")
        return redirect('listado_suscripciones')


class CertificateHardDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Eliminación física de certificado (solo superusuarios)."""
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, uuid):
        certificate = get_object_or_404(Certificate, uuid=uuid)
        certificate.hard_delete()
        log_action(
            user=request.user,
            obj=certificate,
            action_flag=DELETION,
            message=f"Certificado {certificate.pk} eliminado físicamente."
        )
        messages.success(request, "Certificado eliminado permanentemente.")
        return redirect('listado_suscripciones')
