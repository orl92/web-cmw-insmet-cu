from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms.datos.provincias.forms import ProvinceForm
from dashboard.models import Province

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here.
    
class ProvinceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/provincias/provincias.html'
    model = Province
    permission_required = 'dashboard.view_province'  # Permiso requerido para ver las provincias

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Provincias'
        context['parent'] = ''
        context['segment'] = 'provincia'
        context['btn'] = ('Añadir Provincia')
        context['url_create'] = reverse_lazy('crear_provincia')
        context['url_list'] = reverse_lazy('provincias')
        context['objects'] = Province.objects.all()
        return context

class ProvinceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Province
    form_class = ProvinceForm
    template_name = 'pages/dashboard/provincias/crear_provincia.html'
    permission_required = 'dashboard.add_province'  # Permiso requerido para crear una provincia
    success_url = reverse_lazy('provincias')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó una nueva provincia: {self.object.name}."
        )
        
        messages.success(self.request, 'La provincia ha sido creada con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Provincia'
        context['parent'] = ''
        context['segment'] = 'provincia'
        context['url_list'] = reverse_lazy('provincias')
        return context

class ProvinceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Province
    form_class = ProvinceForm
    template_name = 'pages/dashboard/provincias/actualizar_provincia.html'
    permission_required = 'dashboard.change_province'  # Permiso requerido para cambiar una provincia
    success_url = reverse_lazy('provincias')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Province, uuid=uuid)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó la provincia: {self.object.name}."
        )
        
        messages.success(self.request, 'La provincia ha sido actualizada con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Provincia'
        context['parent'] = ''
        context['segment'] = 'provincia'
        context['url_list'] = reverse_lazy('provincias')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class ProvinceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Province
    template_name = 'pages/dashboard/provincias/eliminar_provincia.html'
    permission_required = 'dashboard.delete_province'
    success_url = reverse_lazy('provincias')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Province, uuid=uuid)
    
    def post(self, request, *args, **kwargs):
        province = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=province,
            action_flag=DELETION,
            message=f"Se eliminó la provincia: {province.name}."
        )
        
        try:
            province.delete()
            messages.success(request, 'La provincia ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Provincia'
        context['parent'] = ''
        context['segment'] = 'provincia'
        context['url_list'] = reverse_lazy('provincias')
        return context
