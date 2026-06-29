from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from common.utils import log_action
from dashboard.forms.company.forms import CompanySettingsForm
from dashboard.models import CompanySettings


class CompanySettingsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CompanySettings
    form_class = CompanySettingsForm
    template_name = 'pages/dashboard/company/company_settings.html'
    success_url = reverse_lazy('company_settings')  # La misma vista
    permission_required = 'dashboard.change_companysettings'

    def get_object(self, queryset=None):
        # Singleton: siempre devuelve la instancia con pk=1 (la crea si no existe)
        obj, created = CompanySettings.objects.get_or_create(pk=1)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Datos de Empresa'
        context['parent'] = 'configuracion'
        context['segment'] = 'company_settings'
        context['url_list'] = reverse_lazy('company_settings')
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
