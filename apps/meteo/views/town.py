from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.core.utils import log_action
from apps.meteo.forms.town import TownForm
from apps.meteo.models import Town


class TownListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/meteo/town/list.html'
    model = Town
    permission_required = 'meteo.view_town'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Municipios'
        context['parent'] = ''
        context['segment'] = 'municipio'
        context['btn'] = 'Añadir Municipio'
        context['url_create'] = reverse_lazy('meteo:municipio_create')
        context['url_list'] = reverse_lazy('meteo:municipio_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = self.get_queryset().select_related('province')
        return context

class TownCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Town
    form_class = TownForm
    template_name = 'pages/meteo/town/create.html'
    permission_required = 'meteo.add_town'
    success_url = reverse_lazy('meteo:municipio_list')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
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
        context['url_list'] = reverse_lazy('meteo:municipio_list')
        return context

class TownUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Town
    form_class = TownForm
    template_name = 'pages/meteo/town/update.html'
    permission_required = 'meteo.change_town'
    success_url = reverse_lazy('meteo:municipio_list')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Town, uuid=uuid)

    def form_valid(self, form):
        response = super().form_valid(form)
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
        context['url_list'] = reverse_lazy('meteo:municipio_list')
        return context

    def test_func(self):
        town = self.get_object()
        return self.request.user.is_superuser or town.user == self.request.user

class TownDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'meteo.delete_town'

    def post(self, request, uuid):
        town = get_object_or_404(Town, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=town,
            action_flag=DELETION,
            message=f"Se eliminó el municipio {town.name}."
        )
        try:
            town.delete()
            messages.success(request, 'Municipio eliminado con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('meteo:municipio_list')
