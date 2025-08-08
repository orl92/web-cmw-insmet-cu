from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms.datos.municipios.forms import TownForm
from dashboard.models import Town

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here.
    
class TownListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/municipios/municipios.html'
    model = Town
    permission_required = 'dashboard.view_town'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Municipios'
        context['parent'] = ''
        context['segment'] = 'town'
        context['btn'] = ('Añadir Municipio')
        context['url_create'] = reverse_lazy('crear_municipio')
        context['url_list'] = reverse_lazy('municipios')
        context['objects'] = Town.objects.all()
        return context

class TownCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Town
    form_class = TownForm
    template_name = 'pages/dashboard/municipios/crear_municipio.html'
    permission_required = 'dashboard.add_Town'
    success_url = reverse_lazy('municipios')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo municipio: {self.object.name}."
        )
        
        messages.success(self.request, 'El municipio ha sido creada con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Municipio'
        context['parent'] = ''
        context['segment'] = 'town'
        context['url_list'] = reverse_lazy('municipios')
        return context

class TownUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Town
    form_class = TownForm
    template_name = 'pages/dashboard/municipios/actualizar_municipio.html'
    permission_required = 'dashboard.change_town'
    success_url = reverse_lazy('municipios')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Town, uuid=uuid)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el municipio: {self.object.name}."
        )
        
        messages.success(self.request, 'El municipio ha sido actualizada con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Municipio'
        context['parent'] = ''
        context['segment'] = 'town'
        context['url_list'] = reverse_lazy('municipios')
        return context
    
    def test_func(self):
        # Verifica si el usuario es superusuario o si es el creador del municipio
        town = self.get_object()
        return self.request.user.is_superuser or town.user == self.request.user

class TownDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Town
    template_name = 'pages/dashboard/municipios/eliminar_municipio.html'
    permission_required = 'dashboard.delete_town'
    success_url = reverse_lazy('municipios')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Town, uuid=uuid)

    def post(self, request, *args, **kwargs):
        town = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=town,
            action_flag=DELETION,
            message=f"Se eliminó el municipio: {town.name}."
        )
        
        try:
            town.delete()
            messages.success(request, 'El municipio ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, f'Error al eliminar El municipion: {str(e)}', extra_tags='danger')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Municipio'
        context['parent'] = ''
        context['segment'] = 'town'
        context['url_list'] = reverse_lazy('municipios')
        return context