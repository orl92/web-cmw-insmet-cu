from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.common.utils import log_action
from apps.geo.forms import StationForm
from apps.geo.models import Station


class StationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/estaciones/estaciones.html'
    model = Station
    permission_required = 'geo.view_station'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Estaciones'
        context['parent'] = ''
        context['segment'] = 'estacion'
        context['btn'] = ('Añadir Estación')
        context['url_create'] = reverse_lazy('geo:estacion_create')
        context['url_list'] = reverse_lazy('geo:estacion_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = Station.objects.all().select_related('province')
        return context

class StationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Station
    form_class = StationForm
    template_name = 'pages/dashboard/estaciones/crear_estacion.html'
    permission_required = 'geo.add_station'
    success_url = reverse_lazy('geo:estacion_list')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
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
        context['url_list'] = reverse_lazy('geo:estacion_list')
        return context

class StationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Station
    form_class = StationForm
    template_name = 'pages/dashboard/estaciones/actualizar_estacion.html'
    permission_required = 'geo.change_station'
    success_url = reverse_lazy('geo:estacion_list')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Station, uuid=uuid)

    def form_valid(self, form):
        response = super().form_valid(form)
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
        context['url_list'] = reverse_lazy('geo:estacion_list')
        return context

    def test_func(self):
        station = self.get_object()
        return self.request.user.is_superuser or station.user == self.request.user

class StationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'geo.delete_station'

    def post(self, request, uuid):
        station = get_object_or_404(Station, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=station,
            action_flag=DELETION,
            message=f"Se eliminó la estación {station.name}."
        )
        try:
            station.delete()
            messages.success(request, 'Estación eliminada con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('geo:estacion_list')
