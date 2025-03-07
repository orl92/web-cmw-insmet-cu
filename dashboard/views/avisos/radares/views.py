from datetime import timezone

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import *

from dashboard.forms.avisos.radares.forms import RadarWarningForm
from dashboard.models import RadarWarning

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here.   

class RadarWarningListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = RadarWarning
    template_name = 'pages/dashboard/avisos/radares/avisos_radares.html'
    permission_required = 'dashboard.view_radar_warning'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Avisos Radares'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['btn'] = ('Añadir Aviso Radar')
        context['url_create'] = reverse_lazy('crear_aviso_radar')
        context['url_list'] = reverse_lazy('avisos_radares')
        context['objects'] = RadarWarning.objects.all()
        return context

class RadarWarningCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = RadarWarning
    form_class = RadarWarningForm
    template_name = 'pages/dashboard/avisos/radares/crear_aviso_radar.html'
    permission_required = 'dashboard.add_radar_warning'
    success_url = reverse_lazy('avisos_radares')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo aviso de radar para el: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El aviso de radar ha sido creado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Aviso Radar'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['url_list'] = reverse_lazy('avisos_radares')
        return context

class RadarWarningUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = RadarWarning
    form_class = RadarWarningForm
    template_name = 'pages/dashboard/avisos/radares/actualizar_aviso_radar.html'
    permission_required = 'dashboard.change_radar_warning'
    success_url = reverse_lazy('avisos_radares')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(RadarWarning, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el aviso de radar del: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El aviso de radar ha sido actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso Radar'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['url_list'] = reverse_lazy('avisos_radares')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class RadarWarningDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = RadarWarning
    template_name = 'pages/dashboard/avisos/radares/eliminar_aviso_radar.html'
    permission_required = 'dashboard.delete_radar_warning'
    success_url = reverse_lazy('avisos_radares')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(RadarWarning, uuid=uuid)

    def post(self, request, *args, **kwargs):
        radar_warning = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=radar_warning,
            action_flag=DELETION,
            message=f"Se eliminó el aviso de radar del: {radar_warning.date.strftime('%d-%m-%Y')}."
        )
        
        try:
            radar_warning.delete()
            messages.success(request, 'El aviso de radar ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Aviso Radar'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['url_list'] = reverse_lazy('avisos_radares')
        return context
