from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms.datos.estaciones.forms import StationForm
from dashboard.models import Station

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here.
    
class StationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/estaciones/estaciones.html'
    model = Station
    permission_required = 'dashboard.view_station'  # Permiso requerido para ver una estacion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Estaciones'
        context['parent'] = ''
        context['segment'] = 'estacion'
        context['btn'] = ('Añadir Estación')
        context['url_create'] = reverse_lazy('crear_estacion')
        context['url_list'] = reverse_lazy('estaciones')
        context['objects'] = Station.objects.all()
        return context

class StationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Station
    form_class = StationForm
    template_name = 'pages/dashboard/estaciones/crear_estacion.html'
    permission_required = 'dashboard.add_station'  # Permiso requerido para añadir una estación
    success_url = reverse_lazy('estaciones')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó una nueva estación: {self.object.name}."
        )
        
        messages.success(self.request, 'La estación ha sido creada con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Estación'
        context['parent'] = ''
        context['segment'] = 'estacion'
        context['url_list'] = reverse_lazy('estaciones')
        return context

class StationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Station
    form_class = StationForm
    template_name = 'pages/dashboard/estaciones/actualizar_estacion.html'
    permission_required = 'dashboard.change_station'  # Permiso requerido para cambiar una estación
    success_url = reverse_lazy('estaciones')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Station, uuid=uuid)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó la estación: {self.object.name}."
        )
        
        messages.success(self.request, 'La estación ha sido actualizada con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Estación'
        context['parent'] = ''
        context['segment'] = 'estacion'
        context['url_list'] = reverse_lazy('estaciones')
        return context
    
    def test_func(self):
        # Verifica si el usuario es superusuario o si es el creador de la estación
        station = self.get_object()
        return self.request.user.is_superuser or station.user == self.request.user

class StationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Station
    template_name = 'pages/dashboard/estaciones/eliminar_estacion.html'
    permission_required = 'dashboard.delete_station'  # Permiso requerido para eliminar una estación
    success_url = reverse_lazy('estaciones')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Station, uuid=uuid)

    def post(self, request, *args, **kwargs):
        station = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=station,
            action_flag=DELETION,
            message=f"Se eliminó la estación: {station.name}."
        )
        
        try:
            station.delete()
            messages.success(request, 'La estación ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, f'Error al eliminar la estación: {str(e)}', extra_tags='danger')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Estación'
        context['parent'] = ''
        context['segment'] = 'estacion'
        context['url_list'] = reverse_lazy('estaciones')
        return context