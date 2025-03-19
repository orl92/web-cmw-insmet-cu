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
from dashboard.forms.comentarios.nota_meteorologica.forms import \
    WeatherNoteForm
from dashboard.models import WeatherNote

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here. 

class WeatherNoteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/comentarios/nota_meteorologica/listado_notas_meteorologicas.html'
    model = WeatherNote
    permission_required = 'dashboard.view_weather_note'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Notas Meteorológicas'
        context['parent'] = 'comentario'
        context['segment'] = 'nota_meteorologica'
        context['btn'] = 'Añadir Nota Meteorológica'
        context['url_create'] = reverse_lazy('crear_nota_meteorologica')
        context['url_list'] = reverse_lazy('listado_notas_meteorologicas')
        context['objects'] = WeatherNote.objects.all()
        return context 

class WeatherNoteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = WeatherNote
    form_class = WeatherNoteForm
    template_name = 'pages/dashboard/comentarios/nota_meteorologica/crear_nota_meteorologica.html'
    permission_required = 'dashboard.add_weather_note'
    success_url = reverse_lazy('listado_notas_meteorologicas')
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
            message=f"Se creó una nueva Nota Meteorológica: {self.object.date}."
        )
        
        messages.success(self.request, 'La Nota Meteorológica ha sido creada con éxito.', extra_tags='success')
        
        # Construir la URL dinámica"
        listado_url = self.request.build_absolute_uri(reverse('nota_meteorologica'))
        index_url = self.request.build_absolute_uri(reverse('index'))
        
        # Obtener la lista de correos seleccionada
        recipient_list = self.object.email_recipient_list
        
        if recipient_list:
            recipients = recipient_list.recipients.values_list('email', flat=True)
                
            if recipients:
                # Enviar el correo
                try:
                    # Formatea el campo `date` del modelo antes de incluirlo en el asunto
                    fecha_formateada = self.object.date.strftime("%d-%m-%Y")
                    subject = f"Nota Meteorológica del: {fecha_formateada}"
                    html_message = render_to_string(
                        'pages/dashboard/emails/weather_note.html',
                        {
                            'note': self.object,
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
        
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Nota Meteorológica'
        context['parent'] = 'comentario'
        context['segment'] = 'nota_meteorologica'
        context['url_list'] = reverse_lazy('listado_notas_meteorologicas')
        return context

class WeatherNoteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WeatherNote
    form_class = WeatherNoteForm
    template_name = 'pages/dashboard/comentarios/nota_meteorologica/actualizar_nota_meteorologica.html'
    permission_required = 'dashboard.change_weather_note'
    success_url = reverse_lazy('listado_notas_meteorologicas')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherNote, uuid=uuid) 

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
            action_flag=CHANGE,
            message=f"Se actualizó la Nota Meteorológica del: {self.object.date}."
        )
        
        messages.success(self.request, 'La Nota Meteorológica ha sido actualizada con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Nota Meteorológica'
        context['parent'] = 'comentario'
        context['segment'] = 'nota_meteorologica'
        context['url_list'] = reverse_lazy('listado_notas_meteorologicas')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class WeatherNoteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = WeatherNote
    template_name = 'pages/dashboard/comentarios/nota_meteorologica/eliminar_nota_meteorologica.html'
    permission_required = 'dashboard.delete_weather_note'
    success_url = reverse_lazy('listado_notas_meteorologicas')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherNote, uuid=uuid) 

    def post(self, request, *args, **kwargs):
        weather_note = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=weather_note,
            action_flag=DELETION,
            message=f"Se eliminó la Nota Meteorológica: {weather_note.date}."
        )
        
        try:
            weather_note.delete()
            messages.success(request, 'La nota meteorologica ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Nota Meteorológica'
        context['parent'] = 'comentario'
        context['segment'] = 'nota_meteorologica'
        context['url_list'] = reverse_lazy('listado_notas_meteorologicas')
        return context
