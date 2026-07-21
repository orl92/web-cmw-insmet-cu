from django.contrib import messages
from django.contrib.admin.models import ADDITION, DELETION
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View

from common.utils import log_action
from dashboard.forms.certificados.forms import CertificateForm
from dashboard.models import Certificate


class CertificateListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Certificate
    template_name = 'pages/dashboard/certificados/listado.html'
    permission_required = 'dashboard.view_certificate'

    def get_queryset(self):
        return Certificate.objects.select_related(
            'subscription__customer', 'subscription__service'
        ).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Certificados'
        context['parent'] = ''
        context['segment'] = 'certificados'
        context['btn'] = 'Añadir Certificado'
        context['url_create'] = reverse_lazy('crear_certificado')
        context['url_list'] = reverse_lazy('listado_certificados')
        context['is_superuser'] = self.request.user.is_superuser
        context['url_export'] = reverse_lazy('exportar_csv_certificados')
        context['objects'] = self.get_queryset()
        return context


class CertificateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Certificate
    form_class = CertificateForm
    template_name = 'pages/dashboard/certificados/crear.html'
    permission_required = 'dashboard.add_certificate'
    success_url = reverse_lazy('listado_certificados')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Certificado creado para {self.object.subscription.customer.company_name} - {self.object.subscription.service.title}."
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


class CertificateDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Certificate
    template_name = 'pages/dashboard/certificados/detalle.html'
    permission_required = 'dashboard.view_certificate'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Certificate.objects.select_related('subscription__customer', 'subscription__service'),
            uuid=self.kwargs['uuid']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle del Certificado'
        context['parent'] = ''
        context['segment'] = 'certificados'
        context['url_list'] = reverse_lazy('listado_certificados')
        return context


class CertificatePDFView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.view_certificate'

    def get(self, request, uuid):
        certificate = get_object_or_404(Certificate, uuid=uuid)
        if not certificate.pdf:
            messages.error(request, 'Este certificado no tiene archivo PDF.')
            return redirect('listado_certificados')
        return FileResponse(certificate.pdf.open(), content_type='application/pdf')


class CertificateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_certificate'

    def post(self, request, uuid):
        certificate = get_object_or_404(Certificate, uuid=uuid)
        if not certificate.record_active:
            messages.warning(request, 'El certificado ya estaba desactivado.')
            return redirect('listado_certificados')
        certificate.delete()
        log_action(
            user=self.request.user,
            obj=certificate,
            action_flag=DELETION,
            message=f"Certificado desactivado: {certificate}."
        )
        messages.success(request, 'Certificado desactivado con éxito.')
        return redirect('listado_certificados')
