
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import *

from dashboard.forms.avisos.especiales.forms import SpecialNoticeForm
from dashboard.models import SpecialNotice

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here.    

class SpecialNoticeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/avisos/especiales/avisos_especiales.html'
    model = SpecialNotice
    permission_required = 'dashboard.view_special_notice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Avisos Especiales'
        context['parent'] = 'avisos'
        context['segment'] = 'especial'
        context['btn'] = ('Añadir Aviso Especial')
        context['url_create'] = reverse_lazy('crear_aviso_especial')
        context['url_list'] = reverse_lazy('avisos_especiales')
        context['objects'] = SpecialNotice.objects.all()
        return context

class SpecialNoticeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SpecialNotice
    form_class = SpecialNoticeForm
    template_name = 'pages/dashboard/avisos/especiales/crear_aviso_especial.html'
    permission_required = 'dashboard.add_special_notice'
    success_url = reverse_lazy('avisos_especiales')
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
            message=f"Se creó un nuevo aviso especial para el: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El aviso especial ha sido creado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Aviso Especial'
        context['parent'] = 'avisos'
        context['segment'] = 'especial'
        context['url_list'] = reverse_lazy('avisos_especiales')
        return context

class SpecialNoticeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SpecialNotice
    form_class = SpecialNoticeForm
    template_name = 'pages/dashboard/avisos/especiales/actualizar_aviso_especial.html'
    permission_required = 'dashboard.change_special_notice'
    success_url = reverse_lazy('avisos_especiales')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(SpecialNotice, uuid=uuid)

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
            message=f"Se actualizó el aviso especial del: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El aviso especial ha sido actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso Especial'
        context['parent'] = 'avisos'
        context['segment'] = 'especial'
        context['url_list'] = reverse_lazy('avisos_especiales')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class SpecialNoticeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SpecialNotice
    template_name = 'pages/dashboard/avisos/especiales/eliminar_aviso_especial.html'
    permission_required = 'dashboard.delete_special_notice'
    success_url = reverse_lazy('avisos_especiales')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(SpecialNotice, uuid=uuid)

    def post(self, request, *args, **kwargs):
        special_notice = self.get_object()

        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=special_notice,
            action_flag=DELETION,
            message=f"Se eliminó el aviso especial del: {special_notice.date.strftime('%d-%m-%Y')}."
        )

        try:
            special_notice.delete()
            messages.success(request, 'El aviso especial ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Aviso Especial'
        context['parent'] = 'avisos'
        context['segment'] = 'especial'
        context['url_list'] = reverse_lazy('avisos_especiales')
        return context
