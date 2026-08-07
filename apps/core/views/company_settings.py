from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import UpdateView

from apps.core.forms.company_settings import CompanySettingsForm
from apps.core.models import CompanySettings
from apps.core.utils import log_action


class CompanySettingsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CompanySettings
    form_class = CompanySettingsForm
    template_name = 'pages/core/company/settings.html'
    success_url = reverse_lazy('core:company_settings')
    permission_required = 'core.change_companysettings'

    def get_object(self, queryset=None):
        return CompanySettings.get_instance()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Datos de Empresa'
        context['parent'] = 'configuracion'
        context['segment'] = 'core:company_settings'
        context['url_list'] = reverse_lazy('core:company_settings')
        return context

    def form_valid(self, form):
        self.object = form.save()
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message='Configuración de la empresa actualizada',
        )
        messages.success(self.request, 'Configuración guardada correctamente.')
        return redirect(self.success_url)


class CompanySettingsAjaxUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'core.change_companysettings'

    def post(self, request, *args, **kwargs):
        instance = CompanySettings.get_instance()
        form = CompanySettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
