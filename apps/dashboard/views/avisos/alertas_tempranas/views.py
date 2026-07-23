
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
from apps.dashboard.forms.avisos.alertas_tempranas.forms import EarlyWarningForm
from apps.dashboard.models import EarlyWarning

# Create your views here.

class EarlyWarningListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/avisos/alertas_tempranas/alertas_tempranas.html'
    model = EarlyWarning
    permission_required = 'dashboard.view_early_warning'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Alertas Tempranas'
        context['parent'] = 'avisos'
        context['segment'] = 'early'
        context['btn'] = ('Añadir Alerta Temprana')
        context['url_create'] = reverse_lazy('dashboard:alerta_temprana_create')
        context['url_list'] = reverse_lazy('dashboard:alerta_temprana_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = EarlyWarning.objects.all()
        return context


class EarlyWarningCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EarlyWarning
    form_class = EarlyWarningForm
    template_name = 'pages/dashboard/avisos/alertas_tempranas/crear_aviso_alerta_temprana.html'
    permission_required = 'dashboard.add_early_warning'
    success_url = reverse_lazy('dashboard:alerta_temprana_list')

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
            message=f"Se creó una nueva alerta temprana para el: {self.object.date.strftime('%d-%m-%Y')}."
        )

        # Mensaje de éxito
        messages.success(self.request, 'El aviso de alerta temprana ha sido creado con éxito.', extra_tags='success')

        subject = f'Alerta Temprana: {self.object.date}'
        mail_send(self.request, self.object, subject, 'alerta_temprana')

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Alerta Temprana'
        context['parent'] = 'avisos'
        context['segment'] = 'early'
        context['url_list'] = reverse_lazy('dashboard:alerta_temprana_list')
        return context


class EarlyWarningUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EarlyWarning
    form_class = EarlyWarningForm
    template_name = 'pages/dashboard/avisos/alertas_tempranas/actualizar_aviso_alerta_temprana.html'
    permission_required = 'dashboard.change_early_warning'
    success_url = reverse_lazy('dashboard:alerta_temprana_list')

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(EarlyWarning, uuid=uuid)

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
            message=f"Se actualizó el aviso alerta temprana del: {self.object.date.strftime('%d-%m-%Y')}."
        )

        # Enviar correo solo si hay cambios
        if has_changes:
            subject = f'Alerta Temprana Actualizado: {self.object.date}'
            mail_send(self.request, self.object, subject, 'alerta_temprana')

        # Mensaje de éxito en la actualización
        messages.success(self.request, 'El aviso de alerta temprana ha sido actualizado con éxito.',
                         extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso Alerta Temprana'
        context['parent'] = 'avisos'
        context['segment'] = 'early'
        context['url_list'] = reverse_lazy('dashboard:alerta_temprana_list')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user


class EarlyWarningDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_early_warning'

    def post(self, request, uuid):
        early_warning = get_object_or_404(EarlyWarning, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=early_warning,
            action_flag=DELETION,
            message=f"Se eliminó la alerta temprana del: {early_warning.date.strftime('%d-%m-%Y')}."
        )
        try:
            early_warning.delete()
            messages.success(request, 'El aviso de alerta temprana ha sido eliminada con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('dashboard:alerta_temprana_list')
