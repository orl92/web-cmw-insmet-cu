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
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core import settings
from dashboard.forms.comentarios.tiempo.forms import WeatherCommentaryForm
from dashboard.models import WeatherCommentary

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here. 

class WeatherCommentaryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/comentarios/tiempo/listado_comentarios_tiempo.html'
    model = WeatherCommentary
    permission_required = 'dashboard.view_weather_commentary'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Comentarios del Tiempo'
        context['parent'] = 'comentario'
        context['segment'] = 'comentario_tiempo'
        context['btn'] = 'Añadir Comentario del Tiempo'
        context['url_create'] = reverse_lazy('crear_comentario_tiempo')
        context['url_list'] = reverse_lazy('listado_comentarios_tiempo')
        context['objects'] = WeatherCommentary.objects.all()
        return context 

class WeatherCommentaryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = WeatherCommentary
    form_class = WeatherCommentaryForm
    template_name = 'pages/dashboard/comentarios/tiempo/crear_comentario_tiempo.html'
    permission_required = 'dashboard.add_weather_commentary'
    success_url = reverse_lazy('listado_comentarios_tiempo')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.date = timezone.now()
        instance.save()
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo Comentario del Tiempo: {self.object.date}."
        )
        
        messages.success(self.request, 'El Comentario del Tiempo ha sido creado con éxito.', extra_tags='success')
            
        # Construir la URL dinámica"
        listado_url = self.request.build_absolute_uri(reverse('comentario_tiempo'))
        index_url = self.request.build_absolute_uri(reverse('index'))

        # Obtener la lista seleccionada en el formulario
        recipient_list = self.object.email_recipient_list
        
        if recipient_list:
            recipients = recipient_list.recipients.values_list('email', flat=True)
                
            if recipients:
                # Enviar el correo
                try:
                    subject = f"Comentario del Tiempo"
                    html_message = render_to_string(
                        'pages/dashboard/emails/weather_commentary.html',
                        {
                            'commentary': self.object,
                            'listado_url': listado_url,  # Pasa la URL al contexto del correo
                            'index_url': index_url,     # URL al índice de la página
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

                     # Mostrar mensaje de éxito
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
        context['title'] = 'Añadir Comentario del Tiempo'
        context['parent'] = 'comentario'
        context['segment'] = 'comentario_tiempo'
        context['url_list'] = reverse_lazy('listado_comentarios_tiempo')
        return context

class WeatherCommentaryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WeatherCommentary
    form_class = WeatherCommentaryForm
    template_name = 'pages/dashboard/comentarios/tiempo/actualizar_comentario_tiempo.html'
    permission_required = 'dashboard.change_weather_commentary'
    success_url = reverse_lazy('listado_comentarios_tiempo')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherCommentary, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Obtener el objeto original antes de los cambios
        original_object = self.get_object(queryset=None)
        relevant_fields = ['subject', 'detailed_commentary', 'email_recipient_list']
        
        # Detectar cambios en los campos relevantes
        has_changes = any(
            form.cleaned_data[field] != getattr(original_object, field)
            for field in relevant_fields
        )

        # Guardar el formulario actualizado
        instance = form.save(commit=False)
        instance.date = timezone.now()
        instance.save()
        response = super().form_valid(form)

        # Registrar la acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el Comentario del Tiempo del: {self.object.date}."
        )

        # Enviar correos solo si hay cambios
        if has_changes:
            # Construir la URL dinámica"
            listado_url = self.request.build_absolute_uri(reverse('comentario_tiempo'))
            index_url = self.request.build_absolute_uri(reverse('index'))
            
            # Obtener la lista de correos seleccionada
            recipient_list = self.object.email_recipient_list
            
            if recipient_list:
                recipients = recipient_list.recipients.values_list('email', flat=True)
                
                if recipients:
                    # Enviar el correo
                    try:
                        subject = f"Comentario del Tiempo Actualizado"
                        html_message = render_to_string(
                            'pages/dashboard/emails/weather_commentary.html',
                            {
                                'commentary': self.object,
                                'listado_url': listado_url,  # Pasa la URL al contexto del correo
                                'index_url': index_url,     # URL al índice de la página
                                'current_year': datetime.now().year  # Pasa el año actual
                            }
                        )
                        plain_message = strip_tags(html_message)
                        email = EmailMessage(
                            subject=subject,
                            body=html_message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=list(recipients),
                        )
                        email.content_subtype = 'html'
                        email.send()

                        # Mostrar mensaje de éxito
                        messages.success(self.request, 'El correo de notificación ha sido enviado con éxito.', extra_tags='success')
                    except Exception as e:
                        # Manejar errores de envío
                        messages.error(self.request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
                else:
                    messages.warning(self.request, 'La lista de correos seleccionada no tiene destinatarios.', extra_tags='warning')
            else:
                messages.warning(self.request, 'No se seleccionó ninguna lista de correos para esta actualización.', extra_tags='warning')

        # Mensaje de éxito tras la actualización
        messages.success(self.request, 'El Comentario del Tiempo ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Comentario del Tiempo'
        context['parent'] = 'comentario'
        context['segment'] = 'comentario_tiempo'
        context['url_list'] = reverse_lazy('listado_comentarios_tiempo')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class WeatherCommentaryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = WeatherCommentary
    template_name = 'pages/dashboard/comentarios/tiempo/eliminar_comentario_tiempo.html'
    permission_required = 'dashboard.delete_weather_commentary'
    success_url = reverse_lazy('listado_comentarios_tiempo')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherCommentary, uuid=uuid) 

    def post(self, request, *args, **kwargs):
        weather_commentary = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=weather_commentary,
            action_flag=DELETION,
            message=f"Se eliminó el Comentario del Tiempo: {weather_commentary.date}."
        )
        
        try:
            weather_commentary.delete()
            messages.success(request, 'El Comentario del Tiempo ha sido eliminado con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Comentario del Tiempo'
        context['parent'] = 'comentario'
        context['segment'] = 'comentario_tiempo'
        context['url_list'] = reverse_lazy('listado_comentarios_tiempo')
        return context

    model = WeatherCommentary
    template_name = 'pages/dashboard/comentarios/tiempo/eliminar_comentario_tiempo.html'
    permission_required = 'dashboard.delete_weather_commentary'
    success_url = reverse_lazy('listado_comentarios_tiempo')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherCommentary, uuid=uuid) 

    def post(self, request, *args, **kwargs):
        weather_commentary = self.get_object()
        try:
            weather_commentary.delete()
            messages.success(request, 'El comentario del tiempo ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Comentario del Tiempo'
        context['parent'] = 'comentario'
        context['segment'] = 'comentario_tiempo'
        context['url_list'] = reverse_lazy('listado_comentarios_tiempo')
        return context