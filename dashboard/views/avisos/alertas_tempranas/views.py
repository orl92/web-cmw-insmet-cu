from datetime import datetime
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, DetailView

from core import settings
from dashboard.forms.avisos.alertas_tempranas.forms import EarlyWarningForm
from dashboard.models import EarlyWarning

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here.

class EarlyWarningListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/avisos/alertas_tempranas/alertas_tempranas.html'
    model = EarlyWarning
    permission_required = 'dashboard.view_early_warning'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Alertas Tempranas'
        context['parent'] = 'avisos'
        context['segment'] = 'early'
        context['btn'] = ('Añadir Alerta Temprana')
        context['url_create'] = reverse_lazy('crear_aviso_alerta_temprana')
        context['url_list'] = reverse_lazy('alertas_tempranas')
        context['objects'] = EarlyWarning.objects.all()
        return context

class EarlyWarningCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EarlyWarning
    form_class = EarlyWarningForm
    template_name = 'pages/dashboard/avisos/alertas_tempranas/crear_aviso_alerta_temprana.html'
    permission_required = 'dashboard.add_early_warning'
    success_url = reverse_lazy('alertas_tempranas')

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

        # Construir la URL dinámica"
        listado_url = self.request.build_absolute_uri(reverse('alerta_temprana'))
        index_url = self.request.build_absolute_uri(reverse('index'))
        image_url = self.request.build_absolute_uri(self.object.image.url)

        # Obtener la lista seleccionada en el formulario
        recipient_list = self.object.email_recipient_list
        
        if recipient_list:
            recipients = recipient_list.recipients.values_list('email', flat=True)

            if recipients:
                # Enviar correo
                try:
                    subject = f'Alerta Temprana: {self.object.title}'
                    html_message = render_to_string(
                        'pages/dashboard/emails/notification.html',
                        {
                            'alert': self.object,
                            'listado_url': listado_url,  # Pasa la URL al contexto del correo
                            'index_url': index_url,     # URL al índice de la página
                            'image_url': image_url,
                            'current_year': datetime.now().year  # Pasa el año actual
                        }
                    )
                    # Limpia las etiquetas HTML de la descripción, si existe
                    plain_message = strip_tags(html_message)

                    email = EmailMessage(
                        subject=subject,
                        body=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=list(recipients),
                    )
                    email.content_subtype = 'html'  # Asegura que el correo se envíe como HTML
                    email.send()

                    # Mostrar mensaje de éxito para el envío del correo
                    messages.success(self.request, 'El correo de notificación ha sido enviado con éxito.', extra_tags='success')
                except Exception as e:
                    # Manejar errores de envío
                    messages.error(self.request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
            else:
                messages.warning(self.request, 'La lista de correos seleccionada no tiene destinatarios.', extra_tags='warning')
        else:
            messages.warning(self.request, 'No se seleccionó ninguna lista de correos para esta actualización.', extra_tags='warning')
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Alerta Temprana'
        context['parent'] = 'avisos'
        context['segment'] = 'early'
        context['url_list'] = reverse_lazy('alertas_tempranas')
        return context

class EarlyWarningUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EarlyWarning
    form_class = EarlyWarningForm
    template_name = 'pages/dashboard/avisos/alertas_tempranas/actualizar_aviso_alerta_temprana.html'
    permission_required = 'dashboard.change_early_warning'
    success_url = reverse_lazy('alertas_tempranas')

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
        relevant_fields = ['title', 'description', 'valid_until']
        
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
            # Construir la URL dinámica para el listado de alertas
            listado_url = self.request.build_absolute_uri(reverse('alerta_temprana'))  # Genera la URL completa
            index_url = self.request.build_absolute_uri(reverse('index'))
            image_url = self.request.build_absolute_uri(self.object.image.url)
            
            # Obtener la lista de destinatarios seleccionada
            recipient_list = self.object.email_recipient_list
            
            if recipient_list:
                recipients = recipient_list.recipients.values_list('email', flat=True)
                
                from django.utils.html import strip_tags
                
                # Renderizar el correo electrónico
                subject = f'Alerta Temprana Actualizada: {self.object.title}'
                html_message = render_to_string(
                    'pages/dashboard/emails/notification.html',
                    {
                        'alert': self.object,
                        'listado_url': listado_url,
                        'index_url': index_url,     # URL al índice de la página
                        'image_url': image_url,
                        'current_year': datetime.now().year  # Pasa el año actual
                    }
                )

                # Limpia la descripción de etiquetas HTML
                plain_description = strip_tags(self.object.description)

                plain_message = strip_tags(html_message).replace(self.object.description, plain_description)

                try:
                    email = EmailMessage(
                        subject=subject,
                        body=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=list(recipients),
                    )
                    email.content_subtype = 'html'
                    email.send()

                    # Mostrar un mensaje de éxito si el correo se envía correctamente
                    messages.success(self.request, 'El correo de notificación ha sido enviado con éxito.', extra_tags='success')
                except Exception as e:
                    # Manejar errores y mostrar un mensaje al usuario
                    messages.error(self.request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
            else:
                messages.warning(self.request, 'No se seleccionó ninguna lista de correos para esta alerta.', extra_tags='warning')

        # Mensaje de éxito en la actualización
        messages.success(self.request, 'El aviso de alerta temprana ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso Alerta Temprana'
        context['parent'] = 'avisos'
        context['segment'] = 'early'
        context['url_list'] = reverse_lazy('alertas_tempranas')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class EarlyWarningDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = EarlyWarning
    template_name = 'pages/dashboard/avisos/alertas_tempranas/eliminar_aviso_alerta_temprana.html'
    permission_required = 'dashboard.delete_early_warning'
    success_url = reverse_lazy('alertas_tempranas')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(EarlyWarning, uuid=uuid)

    def post(self, request, *args, **kwargs):
        early_warning = self.get_object()

        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=early_warning,
            action_flag=DELETION,
            message=f"Se eliminó la alerta temprana del: {early_warning.date.strftime('%d-%m-%Y')}."
        )

        try:
            early_warning.delete()
            messages.success(request, 'El aviso de alerta temprana ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Aviso Alerta Temprana'
        context['parent'] = 'avisos'
        context['segment'] = 'early'
        context['url_list'] = reverse_lazy('alertas_tempranas')
        return context

class EarlyWarningDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = EarlyWarning
    template_name = 'pages/dashboard/avisos/alertas_tempranas/detalle_alerta_temprana.html'
    permission_required = 'dashboard.view_early_warning'
    context_object_name = 'early'  # Nombre del objeto en el contexto

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(EarlyWarning, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle del Aviso Alerta Temprana'
        context['parent'] = 'avisos'
        context['segment'] = 'early'
        context['url_list'] = reverse_lazy('alertas_tempranas')
        return context