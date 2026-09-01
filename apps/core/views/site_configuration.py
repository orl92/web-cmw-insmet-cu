from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from apps.core.forms.site_configuration import SiteConfigurationForm
from apps.core.models import SiteConfiguration
from apps.core.utils import log_action


class SiteConfigurationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SiteConfiguration
    form_class = SiteConfigurationForm
    template_name = 'pages/core/site/settings.html'
    success_url = reverse_lazy('core:site_configuration')
    permission_required = 'core.change_siteconfiguration'

    def get_object(self, queryset=None):
        return SiteConfiguration.get_instance()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Configuración del sitio'
        context['parent'] = 'configuracion'
        context['segment'] = 'core:site_configuration'
        context['url_list'] = reverse_lazy('core:site_configuration')
        return context

    def post(self, request, *args, **kwargs):
        if 'delete_logo' in request.POST:
            site = self.get_object()
            site.brand_logo.delete(save=False)
            site.save()
            log_action(
                user=request.user,
                obj=site,
                action_flag=CHANGE,
                message='Logo del sitio eliminado',
            )
            messages.success(
                self.request, 'El logo ha sido eliminado con éxito.', extra_tags='danger'
            )
            return redirect(self.success_url)
        if 'delete_favicon' in request.POST:
            site = self.get_object()
            site.favicon.delete(save=False)
            site.save()
            log_action(
                user=request.user,
                obj=site,
                action_flag=CHANGE,
                message='Favicon del sitio eliminado',
            )
            messages.success(
                self.request, 'El favicon ha sido eliminado con éxito.', extra_tags='danger'
            )
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message='Configuración del sitio actualizada',
        )
        messages.success(self.request, 'Configuración del sitio guardada correctamente.')
        return redirect(self.success_url)
