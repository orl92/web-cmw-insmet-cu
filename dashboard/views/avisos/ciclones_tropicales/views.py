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
from dashboard.forms.avisos.ciclones_tropicales.forms import \
    TropicalCycloneForm
from dashboard.models import TropicalCyclone, EmailRecipientList

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here. 

class TropicalCycloneListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/avisos_ciclones_tropicales.html'
    model = TropicalCyclone
    permission_required = 'dashboard.view_tropical_cyclone'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ciclones Tropicales'
        context['parent'] = 'avisos'
        context['segment'] = 'ciclon-tropical'
        context['btn'] = ('Añadir Aviso Ciclón Tropical')
        context['url_create'] = reverse_lazy('crear_aviso_ciclon_tropical')
        context['url_list'] = reverse_lazy('ciclones_tropicales')
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
        
        # Construir la URL dinámica para "Ver todas las alertas"
        listado_url = self.request.build_absolute_uri(reverse('ciclon_tropical'))

        # Obtener la lista seleccionada en el formulario
        recipient_list = self.object.email_recipient_list
        if recipient_list:
            recipients = recipient_list.recipients.values_list('email', flat=True)

            # Enviar correo
            subject = f'Nueva Alerta de Ciclón Tropical: {self.object.title}'
            html_message = render_to_string(
                'pages/dashboard/emails/tropical_cyclone_notification.html',
                {
                    'alert': self.object,
                    'listado_url': listado_url
                }
            )
            plain_message = strip_tags(html_message)

            try:
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=list(recipients),
                )
                email.content_subtype = 'html'
                email.send()

                # Mensaje de éxito para el envío del correo
                messages.success(self.request, 'El correo de notificación ha sido enviado con éxito.', extra_tags='success')
            except Exception as e:
                # Manejar errores de envío
                messages.error(self.request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
        else:
            messages.warning(self.request, 'No se seleccionó ninguna lista de correos para esta alerta.', extra_tags='warning')
        
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Aviso Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'ciclon-tropical'
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
            message=f"Se actualizó el aviso de ciclón tropical del: {self.object.date.strftime('%d-%m-%Y')}."
        )

        # Enviar correo solo si hay cambios
        if has_changes:
            listado_url = self.request.build_absolute_uri(reverse('ciclon_tropical'))
            recipient_list = self.object.email_recipient_list

            if recipient_list:
                recipients = recipient_list.recipients.values_list('email', flat=True)

                from django.utils.html import strip_tags

                # Renderizar el correo electrónico
                subject = f'Alerta de Ciclón Tropical Actualizada: {self.object.title}'
                html_message = render_to_string(
                    'pages/dashboard/emails/tropical_cyclone_update_notification.html',
                    {'alert': self.object, 'listado_url': listado_url}
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
        messages.success(self.request, 'El aviso de ciclón tropical ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'ciclon-tropical'
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class TropicalCycloneDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TropicalCyclone
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/eliminar_aviso_ciclon_tropical.html'
    permission_required = 'dashboard.delete_tropical_cyclone'
    success_url = reverse_lazy('ciclones_tropicales')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(TropicalCyclone, uuid=uuid)

    def post(self, request, *args, **kwargs):
        tropical_cyclone = self.get_object()

        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=tropical_cyclone,
            action_flag=DELETION,
            message=f"Se eliminó el aviso de ciclón tropical del: {tropical_cyclone.date.strftime('%d-%m-%Y')}."
        )

        try:
            tropical_cyclone.delete()
            messages.success(request, 'El aviso de ciclón tropical ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Aviso Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'ciclon-tropical'
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        return context
