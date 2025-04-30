
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
from django.views.generic import *

from core import settings
from dashboard.forms.avisos.tormentas.forms import StormWarningForm
from dashboard.models import StormWarning

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here.    

class StormWarningListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/avisos/tormentas/avisos_tormentas.html'
    model = StormWarning
    permission_required = 'dashboard.view_storm_warning'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Avisos de Tormentas'
        context['parent'] = 'avisos'
        context['segment'] = 'storm'
        context['btn'] = ('Añadir Aviso de Tormenta')
        context['url_create'] = reverse_lazy('crear_aviso_tormenta')
        context['url_list'] = reverse_lazy('avisos_tormentas')
        context['objects'] = StormWarning.objects.all()
        return context

class StormWarningCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = StormWarning
    form_class = StormWarningForm
    template_name = 'pages/dashboard/avisos/tormentas/crear_aviso_tormenta.html'
    permission_required = 'dashboard.add_storm_warning'
    success_url = reverse_lazy('avisos_tormentas')
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
        
        # Construir la URL dinámica para "Ver todas las alertas"
        listado_url = self.request.build_absolute_uri(reverse('tormenta'))
        index_url = self.request.build_absolute_uri(reverse('index'))
        image_url = self.request.build_absolute_uri(self.object.image.url)

        # Obtener la lista seleccionada en el formulario
        recipient_list = self.object.email_recipient_list
        
        if recipient_list:
            recipients = recipient_list.recipients.values_list('email', flat=True)

            if recipients:
                # Enviar correo
                try:
                    subject = f'Aviso de Tormenta: {self.object.title}'
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
                    # Limpia las etiquetas HTML de la descripción, si existe
                    plain_message = strip_tags(html_message)
           
                    email = EmailMessage(
                        subject=subject,
                        body=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=list(recipients),
                    )
                    email.content_subtype = 'html'
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
        context['title'] = 'Añadir Aviso de Tormenta'
        context['parent'] = 'avisos'
        context['segment'] = 'storm'
        context['url_list'] = reverse_lazy('avisos_tormentas')
        return context

class StormWarningUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StormWarning
    form_class = StormWarningForm
    template_name = 'pages/dashboard/avisos/tormentas/actualizar_aviso_tormenta.html'
    permission_required = 'dashboard.change_storm_warning'
    success_url = reverse_lazy('avisos_tormentas')
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
            message=f"Se actualizó el aviso de tormenta del: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        # Enviar correo solo si hay cambios
        if has_changes:
            # Construir la URL dinámica para el listado de alertas
            listado_url = self.request.build_absolute_uri(reverse('tormenta'))
            index_url = self.request.build_absolute_uri(reverse('index'))
            image_url = self.request.build_absolute_uri(self.object.image.url)
            
            # Obtener la lista de destinatarios seleccionada
            recipient_list = self.object.email_recipient_list

            if recipient_list:
                recipients = recipient_list.recipients.values_list('email', flat=True)

                from django.utils.html import strip_tags

                # Renderizar el correo electrónico
                subject = f'Aviso de Tormenta Actualizado: {self.object.title}'
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

                    # Mensaje de éxito del envío de correos
                    messages.success(self.request, 'El correo de notificación ha sido enviado con éxito.', extra_tags='success')
                except Exception as e:
                    # Manejo de errores en el envío de correos
                    messages.error(self.request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
            else:
                # Notificación si no hay destinatarios seleccionados
                messages.warning(self.request, 'No se seleccionó ninguna lista de correos para esta alerta.', extra_tags='warning')
        
        # Mensaje de éxito en la actualización del aviso
        messages.success(self.request, 'El aviso de tormenta ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso de Tormenta'
        context['parent'] = 'avisos'
        context['segment'] = 'storm'
        context['url_list'] = reverse_lazy('avisos_tormentas')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class StormWarningDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = StormWarning
    template_name = 'pages/dashboard/avisos/tormentas/eliminar_aviso_tormenta.html'
    permission_required = 'dashboard.delete_storm_warning'
    success_url = reverse_lazy('avisos_tormentas')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(StormWarning, uuid=uuid)

    def post(self, request, *args, **kwargs):
        special_notice = self.get_object()

        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=special_notice,
            action_flag=DELETION,
            message=f"Se eliminó el aviso de tormenta del: {special_notice.date.strftime('%d-%m-%Y')}."
        )

        try:
            special_notice.delete()
            messages.success(request, 'El aviso de tormenta ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Aviso de Tormenta'
        context['parent'] = 'avisos'
        context['segment'] = 'storm'
        context['url_list'] = reverse_lazy('avisos_tormentas')
        return context

class StormWarningDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = StormWarning
    template_name = 'pages/dashboard/avisos/tormentas/detalle_aviso_tormenta.html'
    permission_required = 'dashboard.view_storm_warning'
    context_object_name = 'storm'  # Nombre del objeto en el contexto

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(StormWarning, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle del Aviso de Tormenta'
        context['parent'] = 'avisos'
        context['segment'] = 'storm'
        context['url_list'] = reverse_lazy('avisos_tormentas')
        return context