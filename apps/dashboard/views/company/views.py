from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from apps.common.utils import log_action
from apps.dashboard.forms.company.forms import CompanySettingsForm
from apps.dashboard.models import CompanySettings


class CompanySettingsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CompanySettings
    form_class = CompanySettingsForm
    template_name = 'pages/dashboard/company/company_settings.html'
    success_url = reverse_lazy('dashboard:company_settings')  # La misma vista
    permission_required = 'dashboard.change_company_settings'

    def get_object(self, queryset=None):
        return CompanySettings.get_instance()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Datos de Empresa'
        context['parent'] = 'configuracion'
        context['segment'] = 'dashboard:company_settings'
        context['url_list'] = reverse_lazy('dashboard:company_settings')
        return context

    def form_valid(self, form):
        self.object = form.save()
        
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message="Configuración de la empresa actualizada"
        )
        messages.success(self.request, "Configuración guardada correctamente.")
        return redirect(self.success_url)
