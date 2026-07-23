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
from apps.geo.forms import ProvinceForm
from apps.geo.models import Province


class ProvinceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/provincias/provincias.html'
    model = Province
    permission_required = 'geo.view_province'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Provincias'
        context['parent'] = ''
        context['segment'] = 'provincia'
        context['btn'] = ('Añadir Provincia')
        context['url_create'] = reverse_lazy('geo:provincia_create')
        context['url_list'] = reverse_lazy('geo:provincia_list')
        context['is_superuser'] = self.request.user.is_superuser
        return context

class ProvinceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Province
    form_class = ProvinceForm
    template_name = 'pages/dashboard/provincias/crear_provincia.html'
    permission_required = 'geo.add_province'
    success_url = reverse_lazy('geo:provincia_list')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
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
        context['url_list'] = reverse_lazy('geo:provincia_list')
        return context

class ProvinceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Province
    form_class = ProvinceForm
    template_name = 'pages/dashboard/provincias/actualizar_provincia.html'
    permission_required = 'geo.change_province'
    success_url = reverse_lazy('geo:provincia_list')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Province, uuid=uuid)

    def form_valid(self, form):
        response = super().form_valid(form)
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
        context['url_list'] = reverse_lazy('geo:provincia_list')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class ProvinceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'geo.delete_province'

    def post(self, request, uuid):
        province = get_object_or_404(Province, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=province,
            action_flag=DELETION,
            message=f"Se eliminó la provincia {province.name}."
        )
        try:
            province.delete()
            messages.success(request, 'Provincia eliminada con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('geo:provincia_list')
