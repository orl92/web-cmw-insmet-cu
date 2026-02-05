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
    UserPassesTestMixin,
)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from common.utils import log_action

from dashboard.data.mail_send import mail_send
from dashboard.forms.comentarios.tiempo.forms import WeatherCommentaryForm
from dashboard.models import WeatherCommentary

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
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
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

        subject = 'Comentario del Tiempo'
        mail_send(self.request, self.object, subject, 'comentario_tiempo')
        
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

        # Registrar la acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el Comentario del Tiempo del: {self.object.date}."
        )

        # Enviar correos solo si hay cambios
        if has_changes:
            subject = 'Comentario del Tiempo Actualizado'
            mail_send(self.request, self.object, subject, 'comentario_tiempo')

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

    def get_object(self, queryset=None):  # noqa: F811
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherCommentary, uuid=uuid) 

    def post(self, request, *args, **kwargs):  # noqa: F811
        weather_commentary = self.get_object()
        try:
            weather_commentary.delete()
            messages.success(request, 'El comentario del tiempo ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):  # noqa: F811
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Comentario del Tiempo'
        context['parent'] = 'comentario'
        context['segment'] = 'comentario_tiempo'
        context['url_list'] = reverse_lazy('listado_comentarios_tiempo')
        return context
    
class WeatherCommentaryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherCommentary
    template_name = 'pages/dashboard/comentarios/tiempo/detalle_comentario_tiempo.html'
    permission_required = 'dashboard.view_weather_commentary'
    context_object_name = 'weather_commentary'  # Nombre del objeto en el contexto

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherCommentary, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle Comentario del Tiempo'
        context['parent'] = 'comentario'
        context['segment'] = 'comentario_tiempo'
        context['url_list'] = reverse_lazy('listado_comentarios_tiempo')
        return context
    
class WeatherCommentaryPDFView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherCommentary
    permission_required = 'dashboard.view_weather_commentary'

    def get(self, request, *args, **kwargs):
        weather_commentary = self.get_object()

        # Obtener imagen en formato Base64
        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)

        # Renderizar template HTML
        template = get_template('pages/dashboard/comentarios/tiempo/pdf_template.html')
        context = {'weather_commentary': weather_commentary, 'logo_base64': logo_base64}
        html = template.render(context)

        # Crear PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"comentario_tiempo_{weather_commentary.date.strftime('%Y-%m-%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherCommentary, uuid=uuid)

    @staticmethod
    def get_image_base64(image_path):
        """Convierte la imagen en Base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
