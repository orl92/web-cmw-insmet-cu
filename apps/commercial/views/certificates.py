from django.contrib import messages
from django.contrib.admin.models import ADDITION, DELETION
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, View

from apps.commercial.forms.certificate import CertificateForm
from apps.commercial.models import Certificate
from apps.core.utils import log_action


class CertificateListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Certificate
    template_name = 'pages/commercial/certificate/list.html'
    permission_required = 'commercial.view_certificate'
    context_object_name = 'objects'

    def get_queryset(self):
        # `customer__user` porque la columna Cliente muestra `display_name`,
        # que para una persona natural lee los nombres del User.
        return Certificate.objects.select_related(
            'subscription__customer__user', 'subscription__service'
        ).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Certificados'
        context['parent'] = ''
        context['segment'] = 'certificados'
        context['btn'] = 'Añadir Certificado'
        context['url_create'] = reverse_lazy('commercial:certificado_create')
        context['url_list'] = reverse_lazy('commercial:certificado_list')
        context['is_superuser'] = self.request.user.is_superuser
        return context


class CertificateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Certificate
    form_class = CertificateForm
    template_name = 'pages/commercial/certificate/create.html'
    permission_required = 'commercial.add_certificate'
    success_url = reverse_lazy('commercial:certificado_list')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=(
                f'Certificado creado para '
                f'{self.object.subscription.customer.company_name} - '
                f'{self.object.subscription.service.title}.'
            ),
        )
        messages.success(self.request, 'Certificado creado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Certificado'
        context['parent'] = ''
        context['segment'] = 'certificados'
        context['url_list'] = self.success_url
        return context


class CertificatePDFView(LoginRequiredMixin, View):
    """Sirve el PDF de un certificado.

    Acceso: staff con ``commercial.view_certificate`` o el cliente titular de
    la suscripción del certificado (las páginas "Mis Servicios" y "Mis
    Suscripciones" incrustan el certificado en el modal). Cualquier otro
    usuario recibe 403.
    """

    permission_required = 'commercial.view_certificate'

    def has_permission(self, certificate):
        user = self.request.user
        if user.has_perm(self.permission_required):
            return True
        if not hasattr(user, 'commercial_customer'):
            return False
        return certificate.subscription.customer_id == user.commercial_customer.pk

    def get(self, request, uuid):
        certificate = get_object_or_404(
            Certificate.objects.select_related('subscription'), uuid=uuid
        )
        if not self.has_permission(certificate):
            raise PermissionDenied
        if not certificate.pdf:
            messages.error(request, 'Este certificado no tiene archivo PDF.')
            return redirect('commercial:certificado_list')
        response = FileResponse(certificate.pdf.open(), content_type='application/pdf')
        disposition = 'inline' if request.GET.get('inline') else 'attachment'
        response['Content-Disposition'] = (
            f'{disposition}; filename="certificado_{certificate.issued_date:%Y-%m-%d}.pdf"'
        )
        # Same as ServeModelFileView: let the PDF modal embed this same-origin
        # document (Firefox treats <object> as a frame and the global
        # X-Frame-Options: DENY would block the inline preview).
        if disposition == 'inline':
            response['X-Frame-Options'] = 'SAMEORIGIN'
        return response


class CertificateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'commercial.delete_certificate'

    def post(self, request, uuid):
        certificate = get_object_or_404(Certificate, uuid=uuid)
        if not certificate.record_active:
            messages.warning(request, 'El certificado ya estaba desactivado.')
            return redirect('commercial:certificado_list')
        certificate.delete()
        log_action(
            user=self.request.user,
            obj=certificate,
            action_flag=DELETION,
            message=f'Certificado desactivado: {certificate}.',
        )
        messages.success(request, 'Certificado desactivado con éxito.')
        return redirect('commercial:certificado_list')
