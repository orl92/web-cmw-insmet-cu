
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from common.utils import log_action
from dashboard.data.mail_send import mail_send
from dashboard.forms.avisos.ciclones_tropicales.forms import TropicalCycloneForm
from dashboard.models import TropicalCyclone

# Create your views here. 

class TropicalCycloneListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/avisos_ciclones_tropicales.html'
    model = TropicalCyclone
    permission_required = 'dashboard.view_tropical_cyclone'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ciclones Tropicales'
        context['parent'] = 'avisos'
        context['segment'] = 'cyclone'
        context['btn'] = ('Añadir Aviso Ciclón Tropical')
        context['url_create'] = reverse_lazy('crear_aviso_ciclon_tropical')
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        context['url_export'] = reverse_lazy('exportar_csv_ciclones')
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = TropicalCyclone.objects.all()
        return context

class TropicalCycloneCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TropicalCyclone
    form_class = TropicalCycloneForm
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/crear_aviso_ciclon_tropical.html'
    permission_required = 'dashboard.add_tropical_cyclone'
    success_url = reverse_lazy('ciclones_tropicales')
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
            message=f"Se creó un nuevo aviso de ciclón tropical para el: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El aviso de ciclón tropical ha sido creado con éxito.', extra_tags='success')

        subject = f'Aviso de Ciclon Tropical: {self.object.date}'
        mail_send(self.request, self.object, subject, "ciclon_tropical")

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Aviso Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'cyclone'
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        return context

class TropicalCycloneUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TropicalCyclone
    form_class = TropicalCycloneForm
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/actualizar_aviso_ciclon_tropical.html'
    permission_required = 'dashboard.change_tropical_cyclone'
    success_url = reverse_lazy('ciclones_tropicales')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(TropicalCyclone, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Almacenar los valores originales del objeto antes de cualquier actualización
        original_object = self.get_object(queryset=None)
        relevant_fields = ['summary', 'file', 'valid_until']
        
        # Detectar si hay cambios en los campos relevantes
        has_changes = any(
            form.cleaned_data[field] != getattr(original_object, field)
            for field in relevant_fields
        )

        response = super().form_valid(form)  # Guarda los cambios del formulario

        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el aviso de ciclón tropical del: {self.object.date.strftime('%d-%m-%Y')}."
        )

        # Enviar correo solo si hay cambios
        if has_changes:
            subject = f'Aviso de Ciclon Tropical Actualizado: {self.object.date}'
            mail_send(self.request, self.object, subject, "ciclon_tropical")

        # Mensaje de éxito en la actualización del aviso
        messages.success(self.request, 'El aviso de ciclón tropical ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'cyclone'
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class TropicalCycloneDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_tropical_cyclone'

    def post(self, request, uuid):
        tropical_cyclone = get_object_or_404(TropicalCyclone, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=tropical_cyclone,
            action_flag=DELETION,
            message=f"Se eliminó el aviso de ciclón tropical del: {tropical_cyclone.date.strftime('%d-%m-%Y')}."
        )
        try:
            tropical_cyclone.delete()
            messages.success(request, 'El aviso de ciclón tropical ha sido eliminado con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('ciclones_tropicales')
