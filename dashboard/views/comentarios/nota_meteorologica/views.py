import base64
import os
from io import BytesIO

import xhtml2pdf.pisa as pisa
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from common.utils import log_action
from dashboard.data.mail_send import mail_send
from dashboard.forms.comentarios.nota_meteorologica.forms import WeatherNoteForm
from dashboard.models import WeatherNote

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
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
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

        subject = 'Nota Meteorológica'
        mail_send(self.request, self.object, subject, 'nota_meteorologica')
        
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
        # Obtener el objeto original antes de los cambios
        original_object = self.get_object(queryset=None)
        relevant_fields = ['summary', 'file', 'email_recipient_list']
        
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
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó la Nota Meteorológica del: {self.object.date}."
        )
        
        # Enviar correos solo si hay cambios
        if has_changes:
            subject = 'Nota Meteorológica Actualizada'
            mail_send(self.request, self.object, subject, 'nota_meteorologica')
        
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

class WeatherNoteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_weather_note'

    def post(self, request, uuid):
        weather_note = get_object_or_404(WeatherNote, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=weather_note,
            action_flag=DELETION,
            message=f"Se eliminó la nota meteorológica del: {weather_note.date.strftime('%d-%m-%Y')}."
        )
        try:
            weather_note.delete()
            messages.success(request, 'La nota meteorológica ha sido eliminada con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('listado_notas_meteorologicas')

class WeatherNoteDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherNote
    template_name = 'pages/dashboard/comentarios/nota_meteorologica/detalle_nota_meteorologica.html'
    permission_required = 'dashboard.view_weather_note'
    context_object_name = 'weather_note'  # Nombre del objeto en el contexto

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherNote, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle de la Nota Meteorológica'
        context['parent'] = 'comentario'
        context['segment'] = 'nota_meteorologica'
        context['url_list'] = reverse_lazy('listado_notas_meteorologicas')
        return context      
        
class WeatherNotePDFView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherNote
    permission_required = 'dashboard.view_weather_note'

    def get(self, request, *args, **kwargs):
        weather_note = self.get_object()

        # Obtener imagen en formato Base64
        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)
        
        # Renderizar template HTML
        template = get_template('pages/dashboard/comentarios/nota_meteorologica/pdf_template.html')
        context = {'weather_note': weather_note, 'logo_base64': logo_base64}
        html = template.render(context)

        # Crear PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"nota_meteorologica_{weather_note.date.strftime('%Y-%m-%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherNote, uuid=uuid)

    @staticmethod
    def get_image_base64(image_path):
        """Convierte la imagen en Base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
