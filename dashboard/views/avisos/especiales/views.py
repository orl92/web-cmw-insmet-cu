
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
        
        # Mensaje de éxito
        messages.success(self.request, 'El aviso especial ha sido creado con éxito.', extra_tags='success')
        
        # Construir la URL dinámica para "Ver todas las alertas"
        listado_url = self.request.build_absolute_uri(reverse('especial'))
        index_url = self.request.build_absolute_uri(reverse('index'))
        image_url = self.request.build_absolute_uri(self.object.image.url)

        # Obtener la lista seleccionada en el formulario
        recipient_list = self.object.email_recipient_list
        
        if recipient_list:
            recipients = recipient_list.recipients.values_list('email', flat=True)

            if recipients:
                # Enviar correo
                try:
                    subject = f'Aviso Especial: {self.object.title}'
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
            message=f"Se actualizó el aviso especial del: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        # Enviar correo solo si hay cambios
        if has_changes:
            # Construir la URL dinámica para el listado de alertas
            listado_url = self.request.build_absolute_uri(reverse('especial'))
            index_url = self.request.build_absolute_uri(reverse('index'))
            image_url = self.request.build_absolute_uri(self.object.image.url)
            
            # Obtener la lista de destinatarios seleccionada
            recipient_list = self.object.email_recipient_list

            if recipient_list:
                recipients = recipient_list.recipients.values_list('email', flat=True)

                from django.utils.html import strip_tags

                # Renderizar el correo electrónico
                subject = f'Aviso Especial Actualizado: {self.object.title}'
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
        messages.success(self.request, 'El aviso especial ha sido actualizado con éxito.', extra_tags='success')
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
