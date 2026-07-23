
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
from apps.dashboard.data.mail_send import mail_send
from apps.dashboard.forms.avisos.tormentas.forms import StormWarningForm
from apps.dashboard.models import StormWarning

# Create your views here.

class StormWarningListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/avisos/tormentas/avisos_tormentas.html'
    model = StormWarning
    permission_required = 'dashboard.view_storm_warning'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Avisos de Tormentas'
        context['parent'] = 'avisos'
        context['segment'] = 'storm'
        context['btn'] = ('Añadir Aviso de Tormenta')
        context['url_create'] = reverse_lazy('dashboard:tormenta_create')
        context['url_list'] = reverse_lazy('dashboard:tormenta_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = StormWarning.objects.all()
        return context


class StormWarningCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = StormWarning
    form_class = StormWarningForm
    template_name = 'pages/dashboard/avisos/tormentas/crear_aviso_tormenta.html'
    permission_required = 'dashboard.add_storm_warning'
    success_url = reverse_lazy('dashboard:tormenta_list')
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
            message=f"Se creó un nuevo aviso de tormenta para el: {self.object.date.strftime('%d-%m-%Y')}."
        )

        # Mensaje de éxito
        messages.success(self.request, 'El aviso de tormenta ha sido creado con éxito.', extra_tags='success')
        subject = f'Aviso de Tormentas: {self.object.date}'
        mail_send(self.request, self.object, subject, "tormenta")

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Aviso de Tormenta'
        context['parent'] = 'avisos'
        context['segment'] = 'storm'
        context['url_list'] = reverse_lazy('dashboard:tormenta_list')
        return context


class StormWarningUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StormWarning
    form_class = StormWarningForm
    template_name = 'pages/dashboard/avisos/tormentas/actualizar_aviso_tormenta.html'
    permission_required = 'dashboard.change_storm_warning'
    success_url = reverse_lazy('dashboard:tormenta_list')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(StormWarning, uuid=uuid)

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
            message=f"Se actualizó el aviso de tormenta del: {self.object.date.strftime('%d-%m-%Y')}."
        )

        # Enviar correo solo si hay cambios
        if has_changes:
            subject = f'Aviso de Tormentas Actualizado: {self.object.date}'
            mail_send(self.request, self.object, subject, "tormenta")

        # Mensaje de éxito en la actualización del aviso
        messages.success(self.request, 'El aviso de tormenta ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso de Tormenta'
        context['parent'] = 'avisos'
        context['segment'] = 'storm'
        context['url_list'] = reverse_lazy('dashboard:tormenta_list')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user


class StormWarningDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_storm_warning'

    def post(self, request, uuid):
        storm_warning = get_object_or_404(StormWarning, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=storm_warning,
            action_flag=DELETION,
            message=f"Se eliminó el aviso de tormenta del: {storm_warning.date.strftime('%d-%m-%Y')}."
        )
        try:
            storm_warning.delete()
            messages.success(request, 'El aviso de tormenta ha sido eliminado con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('dashboard:tormenta_list')
